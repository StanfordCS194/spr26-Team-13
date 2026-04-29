# API Contracts

This document defines the shared schemas that every subsystem should use. These
are the first files teammates should read before building feature code.

## Source of truth

- Shared Python models: `src/contracts/`
- Shared exercise names and IDs: `src/shared/exercise_catalog.py`
- Shared validation entrypoint: `src/shared/validators.py`
- Test fixtures for example payloads: `tests/fixtures/`

## Canonical contracts

### Program contracts

- `ProgramExercise` in `src/contracts/program.py`
- `TrainingBlock` in `src/contracts/program.py`
- `TrainingDay` in `src/contracts/program.py`
- `TrainingWeek` in `src/contracts/program.py`
- `TrainingProgram` in `src/contracts/program.py`

Use these for imported or generated plans. Ingestion and generation code should
output these models, not custom dictionaries.

Grouped execution such as `Block 1`, supersets, or circuits should be preserved
in `TrainingDay.blocks`. The flat `TrainingDay.exercises` list remains available
for compatibility, but new code should treat blocks as the primary grouping
mechanism when the source document provides them.

### Runtime contracts

- `WorkoutSession` in `src/contracts/session.py`
- `CompletedSet` in `src/contracts/session.py`

Use these for live session state and logged set completion.

### Event contracts

- `RepEvent` in `src/contracts/events.py`
- `DisplayState` in `src/contracts/events.py`

Use `RepEvent` as the sensing-to-runtime handoff. Use `DisplayState` as the
runtime-to-glasses handoff.

### Coaching and export contracts

- `CoachingCue` in `src/contracts/coaching.py`
- `ExportRecord` in `src/contracts/logging.py`
- `WorkoutSummary` in `src/contracts/logging.py`
- `EquipmentItem` and `DeviceCapabilities` in `src/contracts/device.py`

## Contract rules

- Do not create new JSON shapes when a shared contract already exists.
- If a shared contract is missing a field you need, propose a change in a PR and
  notify Person 1 before merging.
- Prefer adding optional fields before changing required fields.
- Keep manual fallbacks represented explicitly, not as comments or assumptions.

## Required integration path

Every subsystem should support this path:

`program import -> normalized program -> live session -> rep/set events -> completed sets -> summary/export`
