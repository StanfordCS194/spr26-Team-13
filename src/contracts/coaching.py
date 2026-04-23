"""Contracts for real-time coaching cues."""

from typing import Optional

from .common import ContractModel, CueModality, TriggerType


class CoachingCue(ContractModel):
    cue_id: str
    exercise_id: str
    trigger_type: TriggerType
    modality: CueModality
    message: str
    priority: int = 0
    evidence_tag: Optional[str] = None
