# Ingestion

Owns program import, parsing, normalization, and ambiguity handling.

Expected output: `TrainingProgram` objects from `src/contracts/program.py`.
When source documents contain grouped work such as `Block 1`, supersets, or
circuits, ingestion should preserve that structure in `TrainingDay.blocks`.
