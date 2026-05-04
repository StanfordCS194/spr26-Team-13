export interface LoggedSet {
  set: number;
  target?: string;
  reps: string;
  load?: string;
  rpe?: string;
  status?: 'complete' | 'modified' | 'skipped';
  note?: string;
}

export interface LoggedExercise {
  id: string;
  name: string;
  planned: string;
  sets: LoggedSet[];
}

export interface CompletedSession {
  id: string;
  date: string;
  title: string;
  program: string;
  duration: string;
  volume: string;
  completion: number;
  prCount: number;
  readiness: string;
  notes: string;
  exercises: LoggedExercise[];
}

export const completedSessions: CompletedSession[] = [
  {
    id: 'session-full-body-1',
    date: 'Apr 29',
    title: 'Full Body 1',
    program: 'James Dargan import',
    duration: '51 min',
    volume: '6,840 lb',
    completion: 94,
    prCount: 2,
    readiness: 'Good',
    notes: 'Held back slightly on cleans. Jump work felt crisp.',
    exercises: [
      {
        id: 'ankle-iso',
        name: 'BB Back Rack SL Ankle Overcoming Iso',
        planned: '3 holds',
        sets: [
          { set: 1, target: '8s', reps: '8s', rpe: '8', status: 'complete' },
          { set: 2, target: '8s', reps: '8s', rpe: '8', status: 'complete' },
          { set: 3, target: '8s', reps: '8s', rpe: '9', status: 'complete' },
        ],
      },
      {
        id: 'clean-pull-hang-clean',
        name: 'Clean Pull + Hang Clean',
        planned: '4 sets',
        sets: [
          { set: 1, target: '2+2', reps: '2+2', load: '75 lb', rpe: '5.5', status: 'complete' },
          { set: 2, target: '1+1', reps: '1+1', load: '95 lb', rpe: '7', status: 'complete' },
          { set: 3, target: '1+1', reps: '1+1', load: '105 lb', rpe: '7', status: 'complete' },
          { set: 4, target: '1+1', reps: '1+1', load: '105 lb', rpe: '7.5', status: 'complete' },
        ],
      },
      {
        id: 'back-rack-step-up',
        name: 'BB Back Rack Step Up',
        planned: '5 sets',
        sets: [
          { set: 1, target: '2-3', reps: '3', load: '95 lb', rpe: '5', status: 'complete' },
          { set: 2, target: '2-3', reps: '3', load: '105 lb', rpe: '6', status: 'complete' },
          { set: 3, target: '3', reps: '3', load: '115 lb', rpe: '7', status: 'complete' },
          { set: 4, target: '3', reps: '3', load: '115 lb', rpe: '7', status: 'complete' },
          { set: 5, target: '3', reps: '2', load: '115 lb', rpe: '8', status: 'modified', note: 'Balance miss' },
        ],
      },
    ],
  },
  {
    id: 'session-day-2',
    date: 'Apr 27',
    title: 'Day 2 - Block Emphasis',
    program: 'James Dargan import',
    duration: '46 min',
    volume: '5,220 lb',
    completion: 100,
    prCount: 1,
    readiness: 'High',
    notes: 'Trap bar positions felt better each set.',
    exercises: [
      {
        id: 'split-squat-iso',
        name: 'BB Split Squat Overcoming Iso',
        planned: '3 holds',
        sets: [
          { set: 1, target: '6s', reps: '6s', rpe: '7', status: 'complete' },
          { set: 2, target: '6s', reps: '6s', rpe: '8', status: 'complete' },
          { set: 3, target: '6s', reps: '6s', rpe: '8', status: 'complete' },
        ],
      },
      {
        id: 'trap-bar-deadlift',
        name: 'Staggered Stance Trap Bar Deadlift',
        planned: '4 sets',
        sets: [
          { set: 1, target: '3', reps: '3', load: '115 lb', rpe: '5.5', status: 'complete' },
          { set: 2, target: '2', reps: '2', load: '135 lb', rpe: '6.5', status: 'complete' },
          { set: 3, target: '2', reps: '2', load: '145 lb', rpe: '7.5', status: 'complete' },
          { set: 4, target: '2', reps: '2', load: '155 lb', rpe: '8', status: 'complete' },
        ],
      },
      {
        id: 'bench-dips',
        name: 'Bench Dips',
        planned: '3 sets',
        sets: [
          { set: 1, target: '8-10', reps: '10', rpe: '7', status: 'complete' },
          { set: 2, target: '8-10', reps: '10', rpe: '8', status: 'complete' },
          { set: 3, target: '8-10', reps: '9', rpe: '9', status: 'complete' },
        ],
      },
    ],
  },
  {
    id: 'session-upper-power',
    date: 'Apr 24',
    title: 'Upper Power',
    program: 'Powerbuilding 5x',
    duration: '38 min',
    volume: '8,120 lb',
    completion: 88,
    prCount: 0,
    readiness: 'Medium',
    notes: 'Skipped final fly set to keep shoulder quiet.',
    exercises: [
      {
        id: 'bench-press',
        name: 'Bench Press',
        planned: '4 x 4',
        sets: [
          { set: 1, target: '4', reps: '4', load: '225 lb', rpe: '8', status: 'complete' },
          { set: 2, target: '4', reps: '4', load: '225 lb', rpe: '8.5', status: 'complete' },
          { set: 3, target: '4', reps: '3', load: '225 lb', rpe: '9', status: 'modified' },
          { set: 4, target: '4', reps: '4', load: '215 lb', rpe: '8', status: 'modified', note: 'Load drop' },
        ],
      },
      {
        id: 'incline-db-press',
        name: 'Incline Dumbbell Press',
        planned: '3 x 8-10',
        sets: [
          { set: 1, target: '8-10', reps: '10', load: '70 lb', rpe: '8', status: 'complete' },
          { set: 2, target: '8-10', reps: '9', load: '70 lb', rpe: '8.5', status: 'complete' },
          { set: 3, target: '8-10', reps: '8', load: '70 lb', rpe: '9', status: 'complete' },
        ],
      },
    ],
  },
];
