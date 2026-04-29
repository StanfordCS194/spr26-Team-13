// 1:1 mirror of src/contracts/program.py — keep these in sync if the Python
// contracts move. Used by the mock parser stub and the Review screen.

export const SourceType = {
  IMAGE: 'image',
  PDF: 'pdf',
  SPREADSHEET: 'spreadsheet',
  TEXT: 'text',
  GENERATED: 'generated',
} as const;
export type SourceType = (typeof SourceType)[keyof typeof SourceType];

export interface ProgramExercise {
  exercise_id: string;
  display_name: string;
  set_count: number;
  rep_target?: string;
  load_target?: string;
  rpe_target?: number;
  rest_seconds?: number;
  notes?: string;
  ambiguity_flags: string[];
}

export interface TrainingDay {
  day_id: string;
  title: string;
  exercises: ProgramExercise[];
  notes?: string;
}

export interface TrainingWeek {
  week_number: number;
  days: TrainingDay[];
}

export interface TrainingProgram {
  program_id: string;
  user_id: string;
  title: string;
  source_type: SourceType;
  weeks: TrainingWeek[];
  parse_confidence?: number;
  needs_user_confirmation: boolean;
}
