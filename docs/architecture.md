# Architecture

## Top-level flow

1. `src/ingestion/` imports or generates a `TrainingProgram`.
2. `src/runtime/` turns that program into a `WorkoutSession`.
3. `src/sensing/` emits `RepEvent` objects while the user lifts.
4. `src/runtime/` converts those events into `CompletedSet` records.
5. `src/glasses/` renders the current `DisplayState` and coaching outputs.
6. `src/app/` and `src/export/` generate summaries and external logs.

## Design rule

The glasses layer is an adapter, not the source of truth. Core workout logic
must still work if the display demo is disabled.
