"""Pillow-backed renderer for overlay widget contracts.

Takes an OverlayState and paints panels, badges, progress bars, and notifications
onto camera frames without knowing where that state came from.
"""

from datetime import datetime
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.contracts import (
    OverlayBadge,
    OverlayNotification,
    OverlayPanel,
    OverlayPlacement,
    OverlayProgressBar,
    OverlayState,
)

BASE_RENDER_WIDTH = 1280
BASE_RENDER_HEIGHT = 720
BASE_PANEL_PADDING_X = 22
BASE_PANEL_PADDING_Y = 20
BASE_LINE_GAP = 10
BASE_TITLE_FONT_PX = 40
BASE_BODY_FONT_PX = 31
BASE_BADGE_FONT_PX = 28
BASE_PROGRESS_FONT_PX = 28
BASE_PROGRESS_PERCENT_PX = 24
BASE_NOTIFICATION_FONT_PX = 32
BASE_FONT_STROKE_PX = 2
BADGE_BOX_OPACITY = 0.94
NOTIFICATION_BOX_OPACITY = 0.92
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]
TEXT_COLORS = {
    "normal": (255, 255, 255),
    "muted": (190, 190, 190),
    "strong": (255, 255, 255),
    "warning": (80, 220, 255),
    "success": (110, 255, 110),
}
TONE_COLORS = {
    "info": (255, 140, 80),
    "success": (90, 210, 90),
    "warning": (70, 200, 255),
    "danger": (90, 90, 255),
}
BAR_COLORS = {
    "blue": (255, 160, 60),
    "green": (80, 220, 80),
    "amber": (70, 210, 255),
    "red": (90, 90, 255),
}


def _style_text(text: str) -> str:
    return text.upper()


def _ui_scale(frame) -> float:
    frame_h, frame_w = frame.shape[:2]
    return max(min(frame_w / BASE_RENDER_WIDTH, frame_h / BASE_RENDER_HEIGHT), 0.5)


def _scaled(value: int, scale: float, minimum: int = 1) -> int:
    return max(minimum, int(round(value * scale)))


@lru_cache(maxsize=64)
def _load_font(font_px: int):
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, font_px)
            except OSError:
                continue
    return ImageFont.load_default()


def _font_metrics(text: str, font_px: int, stroke_px: int) -> tuple[int, int, tuple[int, int, int, int]]:
    styled = _style_text(text)
    font = _load_font(font_px)
    bbox = font.getbbox(styled, stroke_width=stroke_px)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height, bbox


def _resolve_width(frame, placement: OverlayPlacement, scale: float) -> int:
    frame_w = frame.shape[1]
    margin_x = _scaled(placement.margin_x, scale)
    max_width = frame_w - (margin_x * 2)
    preferred_width = _scaled(placement.width, scale, minimum=8)
    return min(max(preferred_width, 8), max_width)


def _box_origin(frame, placement: OverlayPlacement, width: int, height: int, scale: float) -> tuple[int, int]:
    frame_h, frame_w = frame.shape[:2]
    margin_x = _scaled(placement.margin_x, scale)
    margin_y = _scaled(placement.margin_y, scale)
    anchor = placement.anchor

    if "right" in anchor:
        x = frame_w - width - margin_x
    elif "center" in anchor:
        x = max((frame_w - width) // 2, margin_x)
    else:
        x = margin_x

    if anchor.startswith("bottom"):
        y = frame_h - height - margin_y
    elif anchor == "center":
        y = max((frame_h - height) // 2, margin_y)
    else:
        y = margin_y

    return x, y


def _blend_box(frame, x: int, y: int, width: int, height: int, color, opacity: float) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + width, y + height), color, -1)
    cv2.addWeighted(overlay, opacity, frame, 1.0 - opacity, 0, frame)


def _draw_text(frame, text: str, top_left: tuple[int, int], font_px: int, color, stroke_px: int) -> None:
    styled = _style_text(text)
    font = _load_font(font_px)
    width, height, bbox = _font_metrics(styled, font_px, stroke_px)
    pad = max(stroke_px + 3, 4)
    patch_width = max(width + (pad * 2), 1)
    patch_height = max(height + (pad * 2), 1)

    patch = Image.new("RGBA", (patch_width, patch_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    draw_kwargs = {
        "xy": (pad - bbox[0], pad - bbox[1]),
        "text": styled,
        "font": font,
        "fill": (color[2], color[1], color[0], 255),
    }
    if stroke_px > 0:
        draw_kwargs["stroke_width"] = stroke_px
        draw_kwargs["stroke_fill"] = (20, 20, 20, 210)
    draw.text(**draw_kwargs)

    patch_rgba = np.array(patch)
    x, y = top_left
    frame_h, frame_w = frame.shape[:2]
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + patch_width, frame_w)
    y1 = min(y + patch_height, frame_h)
    if x0 >= x1 or y0 >= y1:
        return

    patch_x0 = x0 - x
    patch_y0 = y0 - y
    patch_x1 = patch_x0 + (x1 - x0)
    patch_y1 = patch_y0 + (y1 - y0)
    alpha = patch_rgba[patch_y0:patch_y1, patch_x0:patch_x1, 3:4].astype(np.float32) / 255.0
    patch_bgr = patch_rgba[patch_y0:patch_y1, patch_x0:patch_x1, :3][:, :, ::-1].astype(np.float32)
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = ((patch_bgr * alpha) + (roi * (1.0 - alpha))).astype(np.uint8)


def _text_size(text: str, font_px: int, stroke_px: int) -> tuple[int, int]:
    width, height, _ = _font_metrics(text, font_px, stroke_px)
    return width, height


def _colored_surface_text_style(tone: str) -> tuple[tuple[int, int, int], int]:
    if tone == "danger":
        return (255, 255, 255), 1
    return (12, 12, 12), 0


def _wrap_text(text: str, max_width: int, font_px: int, stroke_px: int) -> list[str]:
    styled = _style_text(text)
    words = styled.split()
    if not words:
        return [styled]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        candidate_width = _text_size(candidate, font_px, stroke_px)[0]
        if candidate_width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


class OverlayRenderer:
    def render(self, frame, state: OverlayState, now: datetime | None = None):
        now = now or datetime.now()
        scale = _ui_scale(frame)

        for panel in sorted(state.panels, key=lambda item: item.priority):
            if panel.visible:
                self._draw_panel(frame, panel, scale)

        for badge in state.badges:
            if badge.visible and (badge.expires_at is None or badge.expires_at > now):
                self._draw_badge(frame, badge, scale)

        for bar in state.progress_bars:
            if bar.visible:
                self._draw_progress_bar(frame, bar, scale)

        for notification in state.notifications:
            if notification.visible and (
                notification.expires_at is None or notification.expires_at > now
            ):
                self._draw_notification(frame, notification, scale)

        return frame

    def _draw_panel(self, frame, panel: OverlayPanel, scale: float) -> None:
        padding_x = _scaled(BASE_PANEL_PADDING_X, scale)
        padding_y = _scaled(BASE_PANEL_PADDING_Y, scale)
        line_gap = _scaled(BASE_LINE_GAP, scale)
        title_font_px = _scaled(BASE_TITLE_FONT_PX, scale)
        body_font_px = _scaled(BASE_BODY_FONT_PX, scale)
        title_stroke_px = _scaled(BASE_FONT_STROKE_PX, scale)
        body_stroke_px = _scaled(BASE_FONT_STROKE_PX, scale)
        width = _resolve_width(frame, panel.placement, scale)
        text_width = width - (padding_x * 2)
        wrapped_lines: list[tuple[str, tuple[int, int, int]]] = []

        for line in panel.lines:
            text = f"{line.label}: {line.value}"
            color = TEXT_COLORS[line.emphasis]
            for wrapped in _wrap_text(text, text_width, body_font_px, body_stroke_px):
                wrapped_lines.append((wrapped, color))

        title_height = 0
        if panel.title:
            title_height = _text_size(panel.title, title_font_px, title_stroke_px)[1]

        body_line_height = _text_size("AG", body_font_px, body_stroke_px)[1]
        total_body_height = max(len(wrapped_lines), 1) * body_line_height
        total_body_gap = max(len(wrapped_lines) - 1, 0) * line_gap
        height = (
            (padding_y * 2)
            + title_height
            + (line_gap if panel.title and wrapped_lines else 0)
            + total_body_height
            + total_body_gap
        )
        x, y = _box_origin(frame, panel.placement, width, height, scale)
        _blend_box(frame, x, y, width, height, (0, 0, 0), panel.opacity)

        cursor_y = y + padding_y
        if panel.title:
            _draw_text(frame, panel.title, (x + padding_x, cursor_y), title_font_px, (255, 255, 255), title_stroke_px)
            cursor_y += title_height + line_gap

        for text, color in wrapped_lines:
            _draw_text(frame, text, (x + padding_x, cursor_y), body_font_px, color, body_stroke_px)
            cursor_y += body_line_height + line_gap

    def _draw_badge(self, frame, badge: OverlayBadge, scale: float) -> None:
        if badge.compact:
            self._draw_compact_badge(frame, badge, scale)
            return

        width = _resolve_width(frame, badge.placement, scale)
        height = _scaled(52, scale)
        x, y = _box_origin(frame, badge.placement, width, height, scale)
        tone = TONE_COLORS[badge.tone]
        _blend_box(frame, x, y, width, height, tone, BADGE_BOX_OPACITY)
        font_px = _scaled(BASE_BADGE_FONT_PX + 2, scale)
        text_color, stroke_px = _colored_surface_text_style(badge.tone)
        text_height = _text_size(badge.text, font_px, stroke_px)[1]
        text_y = y + max((height - text_height) // 2, 0)
        _draw_text(frame, badge.text, (x + _scaled(14, scale), text_y), font_px, text_color, stroke_px)

    def _draw_compact_badge(self, frame, badge: OverlayBadge, scale: float) -> None:
        diameter = _scaled(badge.placement.width, scale, minimum=8)
        x, y = _box_origin(frame, badge.placement, diameter, diameter, scale)
        center = (x + (diameter // 2), y + (diameter // 2))
        cv2.circle(frame, center, diameter // 2, (24, 24, 24), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, center, max((diameter // 2) - 2, 1), TONE_COLORS[badge.tone], -1, lineType=cv2.LINE_AA)

    def _draw_progress_bar(self, frame, bar: OverlayProgressBar, scale: float) -> None:
        width = _resolve_width(frame, bar.placement, scale)
        height = _scaled(70, scale)
        x, y = _box_origin(frame, bar.placement, width, height, scale)
        padding_x = _scaled(14, scale)
        progress_font_px = _scaled(BASE_PROGRESS_FONT_PX, scale)
        percent_font_px = _scaled(BASE_PROGRESS_PERCENT_PX, scale)
        stroke_px = _scaled(BASE_FONT_STROKE_PX, scale)
        label_height = _text_size(bar.label, progress_font_px, stroke_px)[1]
        percent_label = f"{int(round(bar.progress * 100))}%"
        percent_width = _text_size(percent_label, percent_font_px, stroke_px)[0]

        bar_left = x + padding_x
        bar_top = y + _scaled(40, scale)
        bar_right = x + width - padding_x
        bar_bottom = y + _scaled(56, scale)
        progress_width = bar_right - bar_left

        _blend_box(frame, x, y, width, height, (0, 0, 0), 0.55)
        _draw_text(frame, bar.label, (bar_left, y + _scaled(10, scale)), progress_font_px, (255, 255, 255), stroke_px)
        _draw_text(
            frame,
            percent_label,
            (bar_right - percent_width, y + _scaled(12, scale)),
            percent_font_px,
            (220, 220, 220),
            stroke_px,
        )

        cv2.rectangle(frame, (bar_left, bar_top), (bar_right, bar_bottom), (70, 70, 70), -1)
        fill_width = max(0, min(progress_width, int(round(progress_width * bar.progress))))
        cv2.rectangle(
            frame,
            (bar_left, bar_top),
            (bar_left + fill_width, bar_bottom),
            BAR_COLORS[bar.color],
            -1,
        )

    def _draw_notification(self, frame, notification: OverlayNotification, scale: float) -> None:
        padding_x = _scaled(BASE_PANEL_PADDING_X, scale)
        padding_y = _scaled(BASE_PANEL_PADDING_Y, scale)
        line_gap = _scaled(BASE_LINE_GAP, scale)
        font_px = _scaled(BASE_NOTIFICATION_FONT_PX, scale)
        stroke_px = _scaled(BASE_FONT_STROKE_PX, scale)
        width = _resolve_width(frame, notification.placement, scale)
        text_width = width - (padding_x * 2)
        text_color, stroke_px = _colored_surface_text_style(notification.tone)
        wrapped_lines = _wrap_text(notification.message, text_width, font_px, stroke_px)
        line_height = _text_size("AG", font_px, stroke_px)[1]
        height = (
            (padding_y * 2)
            + (len(wrapped_lines) * line_height)
            + (max(len(wrapped_lines) - 1, 0) * line_gap)
        )
        x, y = _box_origin(frame, notification.placement, width, height, scale)
        tone = TONE_COLORS[notification.tone]
        _blend_box(frame, x, y, width, height, tone, NOTIFICATION_BOX_OPACITY)

        cursor_y = y + padding_y
        for line in wrapped_lines:
            line_x = x + padding_x
            if notification.text_align == "center":
                line_width = _text_size(line, font_px, stroke_px)[0]
                line_x = x + max((width - line_width) // 2, padding_x)
            _draw_text(frame, line, (line_x, cursor_y), font_px, text_color, stroke_px)
            cursor_y += line_height + line_gap
