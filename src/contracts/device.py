"""Contracts for device capabilities and detected equipment."""

from typing import Optional

from pydantic import Field

from .common import ContractModel


class EquipmentItem(ContractModel):
    equipment_id: str
    name: str
    category: str
    count: int = Field(default=1, ge=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source: Optional[str] = None


class DeviceCapabilities(ContractModel):
    has_camera: bool = True
    has_speakers: bool = True
    has_display: bool = False
    supports_tap_input: bool = True
    supports_head_gesture: bool = True
