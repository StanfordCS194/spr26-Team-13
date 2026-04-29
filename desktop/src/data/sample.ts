// Sample Day-1 program for the demo. Used by the Parsing screen's "What we found"
// card and the Review screen's exercise table — single source of truth so the two
// screens stay in agreement.

import { SourceType, type ProgramExercise, type TrainingDay, type TrainingProgram } from '../lib/types';

const day1Exercises: ProgramExercise[] = [
  {
    exercise_id: 'bench-press',
    display_name: 'Bench Press',
    set_count: 4,
    rep_target: '4',
    load_target: '225 lb',
    notes: 'Top set, leave 2 in reserve',
    ambiguity_flags: [],
  },
  {
    exercise_id: 'incline-db-press',
    display_name: 'Incline Dumbbell Press',
    set_count: 3,
    rep_target: '8-10',
    load_target: '70 lb',
    notes: 'Pause at bottom',
    ambiguity_flags: [],
  },
  {
    exercise_id: 'weighted-dip',
    display_name: 'Weighted Dip',
    set_count: 3,
    rep_target: '6-8',
    load_target: 'BW + 45 lb',
    notes: 'Lean forward · chest focus',
    ambiguity_flags: [],
  },
  {
    exercise_id: 'cable-fly',
    display_name: 'Cable Fly',
    set_count: 3,
    rep_target: '12-15',
    load_target: '30 lb',
    notes: 'Slow eccentric',
    ambiguity_flags: [],
  },
  {
    exercise_id: 'tricep-pushdown',
    display_name: 'Tricep Pushdown',
    set_count: 3,
    rep_target: '10-12',
    load_target: '60 lb',
    ambiguity_flags: [],
  },
];

const day1: TrainingDay = {
  day_id: 'day-1',
  title: 'Heavy Push',
  exercises: day1Exercises,
};

export const sampleProgram: TrainingProgram = {
  program_id: 'powerbuilding-5x',
  user_id: 'demo-user',
  title: 'Powerbuilding 5x',
  source_type: SourceType.IMAGE,
  weeks: [{ week_number: 1, days: [day1] }],
  parse_confidence: 0.94,
  needs_user_confirmation: true,
};

// Headline copy for the Parsing screen "What we found" card and demo display.
export const sampleProgramMeta = {
  author: 'Jeff Nippard',
  title: sampleProgram.title,
  workouts: 23,
  sets: 78,
  notes: 14,
};
