"""Validation helpers that can be shared by multiple subsystems."""

from src.contracts import TrainingProgram


def validate_program(program: TrainingProgram) -> TrainingProgram:
    """Stub validator used as a single integration point for program checks."""

    return program
