// Single seam for the backend parser. The desktop app posts the selected file to
// the Flask demo API, which runs Docling extraction and Gemini-backed
// normalization before returning the canonical TrainingProgram contract.

import type { TrainingProgram } from './types';

export interface ExtractedPreview {
  markdown?: string | null;
  normalization_mode?: string | null;
}

export interface ParseProgramResult {
  program: TrainingProgram;
  extracted_preview?: ExtractedPreview;
}

export interface ParseProgramOptions {
  userId?: string;
  endpoint?: string;
  signal?: AbortSignal;
}

export async function parseProgram(
  file: File,
  { userId = 'demo-user', endpoint = '/api/programs/parse', signal }: ParseProgramOptions = {},
): Promise<ParseProgramResult> {
  const body = new FormData();
  body.append('user_id', userId);
  body.append('program_file', file);

  const response = await fetch(endpoint, {
    method: 'POST',
    body,
    signal,
  });

  const payload = await readJson(response);
  if (!response.ok) {
    throw new Error(getErrorMessage(payload) ?? `Parser request failed with ${response.status}`);
  }
  if (!payload || typeof payload !== 'object' || !('program' in payload)) {
    throw new Error('Parser response did not include a program.');
  }

  return payload as ParseProgramResult;
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return { error: text };
  }
}

function getErrorMessage(payload: unknown): string | null {
  if (payload && typeof payload === 'object' && 'error' in payload) {
    const message = (payload as { error?: unknown }).error;
    return typeof message === 'string' ? message : null;
  }
  return null;
}
