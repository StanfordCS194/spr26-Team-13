"""Compatibility exports for the assistant package."""

from src.assistant import AssistantAction, handle_action, handle_message, parse_user_message

__all__ = ["AssistantAction", "handle_action", "handle_message", "parse_user_message"]
