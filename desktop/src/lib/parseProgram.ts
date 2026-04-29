// Single seam for the backend parser. Today this is a setTimeout that returns
// the hardcoded sample. When Person 2's ingestion path is ready, swap the
// implementation for a real fetch — the call sites in ParsingScreen / App
// don't need to change.

import { sampleProgram } from '../data/sample';
import type { TrainingProgram } from './types';

export interface ParseProgramOptions {
  /** How long the mock parse should take, in ms. Defaults to 2800ms. */
  delayMs?: number;
}

export async function parseProgram(
  _file: File,
  { delayMs = 2800 }: ParseProgramOptions = {},
): Promise<TrainingProgram> {
  // The mock ignores file content for now. Real backend will read it.
  await new Promise((resolve) => setTimeout(resolve, delayMs));
  return sampleProgram;
}
