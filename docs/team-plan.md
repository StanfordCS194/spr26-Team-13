# Team Plan

This repo is organized so each person can move in parallel without inventing
their own data shapes. The shared contracts are the source of truth.

## Shared folders everyone should know

- `src/contracts/`: canonical shared schemas used across the project
- `src/shared/`: exercise catalog, validators, and other shared constants
- `tests/fixtures/`: sample data for cross-team testing
- `docs/api-contracts.md`: quick guide to the main shared models

If you are unsure where a field or object should live, check `src/contracts/`
first.

## Person ownership

### Person 1

Owns the shared backbone:

- `src/contracts/`
- `src/runtime/`
- `src/shared/`
- `tests/contracts/`
- `tests/integration/`

Responsibilities:

- maintain canonical schemas
- own the live workout session state machine
- review any contract changes from other teammates
- keep the end-to-end integration path working

### Person 2

Owns program ingestion and normalization:

- `src/ingestion/`
- fixture examples under `tests/fixtures/programs/`

Responsibilities:

- parse image, PDF, spreadsheet, and text programs
- normalize imported plans into `TrainingProgram`
- flag ambiguity for user confirmation

### Person 3

Owns sensing and rep detection:

- `src/sensing/`
- fixture examples under `tests/fixtures/sensor_events/`

Responsibilities:

- sensor adapters
- rep/set event detection
- confidence scoring
- fallback path for manual logging when detection fails

### Person 4

Owns companion app summaries and exports:

- `src/app/`
- `src/export/`
- fixture examples under `tests/fixtures/exports/`

Responsibilities:

- post-workout summaries
- history and trend views
- spreadsheet and CSV logging
- image-to-log attachments

### Person 5

Owns the glasses-facing experience layer:

- `src/glasses/`

Responsibilities:

- display demo rendering
- audio coaching output
- tap/head gesture controls
- consume `DisplayState` and `CoachingCue` without adding business logic

## Team rules

- Person 1 reviews changes in `src/contracts/`.
- Every subsystem must be able to run against fixtures before depending on real
  hardware or external services.
- High-risk features must have a fallback path.
- The runtime layer is the central integration point. Other subsystems should
  hand off data through contracts instead of calling each other directly.

## Weekly integration target

Always keep this flow working:

`program upload -> confirm -> start session -> count or log set -> summarize -> export`
