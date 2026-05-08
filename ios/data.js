// Sample data for the iOS prototype.
//
// The frontend never calls a backend directly — it reads the globals on
// `window`. When the parser/API layer ships, the friend doing the backend
// just needs to populate these globals with real data (or replace the file
// entirely). Same swap-the-stub pattern as auth.js.
//
// Globals exposed:
//   PROGRAMS            — list of saved programs shown on the home feed
//   PROGRAM_DETAIL      — exercises for the active program (flat list)
//   PARSED_PROGRAM      — alias for PROGRAM_DETAIL the review screen reads
//   PROGRAM_SAMPLE_LINES — paper-texture lines for the camera placeholder
//   HISTORY             — last few sessions for home + history tabs
//   ACTIVITY            — 12-week heatmap (84 entries, 0..3 intensity)
//   PAST_WORKOUT        — full set-by-set breakdown for one workout

window.PROGRAMS = [
  {
    id: 'powerbuild-5x',
    name: 'Powerbuilding 5×',
    author: 'J. Nippard',
    weeks: 10,
    daysPerWeek: 5,
    type: 'Powerbuilding',
    color: '#C5F23E',
    sourceLabel: 'Spreadsheet · scanned',
    parsedOn: 'Apr 22',
    activeWeek: 3,
    progress: 0.31,
    description:
      '10-week powerbuilding cycle blending heavy strength singles with hypertrophy accessories. Built around squat, bench, deadlift, and OHP percentages.',
  },
  {
    id: 'nsuns-531',
    name: 'nSuns 5/3/1 LP',
    author: 'nSuns',
    weeks: 0, // ongoing
    daysPerWeek: 5,
    type: 'Strength',
    color: '#7DD3FC',
    sourceLabel: 'Imported · text',
    parsedOn: 'Mar 14',
    activeWeek: 0,
    progress: 0,
    description:
      'High-frequency linear progression based on 5/3/1 percentages. Aggressive top-set and back-off scheme.',
  },
  {
    id: 'ppl-arnold',
    name: 'PPL — Arnold Split',
    author: 'Custom',
    weeks: 8,
    daysPerWeek: 6,
    type: 'Hypertrophy',
    color: '#FFC462',
    sourceLabel: 'Photo · handwritten',
    parsedOn: 'Feb 02',
    activeWeek: 0,
    progress: 0,
    description: 'Push-Pull-Legs hypertrophy emphasis. 6 days per week, 8-week block.',
  },
];

// Flat exercise list — used by the program detail view AND the post-parse review.
window.PROGRAM_DETAIL = {
  programId: 'powerbuild-5x',
  exercises: [
    { name: 'Back Squat',           sets: 5, reps: '5',  load: '275 lb', rest: '3 min', note: 'Sit back and down, keep upper back tight to the bar.' },
    { name: 'Barbell Bench Press',  sets: 4, reps: '6',  load: '210 lb', rest: '3 min', note: 'Comfortable arch, quick pause, explode up.' },
    { name: 'Deadlift',             sets: 3, reps: '3',  load: '315 lb', rest: '4 min', note: 'Brace lats, chest tall, pull slack out before lifting.' },
    { name: 'Overhead Press',       sets: 4, reps: '8',  load: '115 lb', rest: '2 min', note: 'Press up and back overhead, slight pause on chest.' },
    { name: 'Pull-Up',              sets: 4, reps: '8',  load: 'BW',     rest: '2 min', note: 'Full hang, chin over the bar.' },
    { name: 'Barbell Row',          sets: 3, reps: '8',  load: '155 lb', rest: '2 min', note: 'Hinge to about 45°, pull to lower chest.' },
    { name: 'Romanian Deadlift',    sets: 3, reps: '10', load: '185 lb', rest: '2 min', note: 'Hips back, soft knees, stretch the hamstrings.' },
    { name: 'Dumbbell Curl',        sets: 3, reps: '12', load: '35 lb',  rest: '90 s',  note: 'Elbows pinned, no swing.' },
    { name: 'Tricep Pushdown',      sets: 3, reps: '12', load: '60 lb',  rest: '90 s',  note: 'Lock elbows at sides, full extension.' },
    { name: 'Standing Calf Raise',  sets: 3, reps: '15', load: '180 lb', rest: '90 s',  note: 'Pause at the top, full stretch at the bottom.' },
    { name: 'Hanging Leg Raise',    sets: 3, reps: '12', load: 'BW',     rest: '60 s',  note: 'Knees to chest, controlled.' },
  ],
};

// The review screen historically read from PARSED_PROGRAM. Alias it so
// existing code keeps working — backend can swap either one.
window.PARSED_PROGRAM = window.PROGRAM_DETAIL;

// Lines drawn on the camera "paper" placeholder + the parsing thumb.
window.PROGRAM_SAMPLE_LINES = [
  'Back Squat (Top Single) · 1×1 @ 87.5%',
  'Back Squat · 5×3 @ 77.5%',
  'OHP · 3×8',
  'Pin Good Morning · 2×8-10',
  'Chest-Sup. Row · 4×8-10',
  'Hanging Leg Raise · 3×10',
];

window.HISTORY = [
  { date: 'Apr 25', day: 'Sat', name: 'Full Body 5', volume: '12,840 lbs', duration: '68m', sets: 17, prs: 1, rpe: 8.2 },
  { date: 'Apr 23', day: 'Thu', name: 'Rest',        volume: '—',          duration: '—',   sets: 0,  prs: 0, rpe: 0   },
  { date: 'Apr 22', day: 'Wed', name: 'Full Body 3', volume: '18,200 lbs', duration: '74m', sets: 14, prs: 0, rpe: 7.8 },
  { date: 'Apr 21', day: 'Tue', name: 'Full Body 2', volume: '15,420 lbs', duration: '82m', sets: 19, prs: 0, rpe: 8.0 },
  { date: 'Apr 20', day: 'Mon', name: 'Full Body 1', volume: '21,640 lbs', duration: '78m', sets: 18, prs: 2, rpe: 8.4 },
  { date: 'Apr 18', day: 'Sat', name: 'Full Body 5', volume: '11,920 lbs', duration: '64m', sets: 16, prs: 0, rpe: 7.6 },
];

// Activity heatmap — last 12 weeks (84 days). 0=none, 1=light, 2=moderate, 3=heavy.
window.ACTIVITY = (() => [
  0,2,2,0,3,2,0, 2,2,0,3,2,2,0, 0,2,3,0,2,2,0, 2,0,2,2,3,2,0,
  2,2,2,0,2,2,0, 2,3,2,0,3,2,0, 0,2,2,2,3,2,0, 2,2,0,3,2,2,0,
  2,3,2,0,2,3,0, 2,2,2,0,2,2,0, 0,3,2,0,3,2,0, 2,2,0,2,2,1,0,
])();

// Past workout summary — for the post-finish landing + tapping a calendar day.
window.PAST_WORKOUT = {
  date: 'Mon · Apr 20',
  name: 'Full Body 1',
  week: 'Week 3',
  totalVolume: '21,640 lbs',
  duration: '78m',
  sets: 18,
  autoTracked: 0.94,
  rpe: 8.4,
  prs: ['Back Squat top single — 365 lb @ RPE 8'],
  exercises: [
    { name: 'Back Squat (Top Single)', sets: [{ reps: 1, load: '365 lb', rpe: 8, status: 'auto' }] },
    { name: 'Back Squat', sets: [
      { reps: 3, load: '320 lb', rpe: 6, status: 'auto' },
      { reps: 3, load: '320 lb', rpe: 6, status: 'auto' },
      { reps: 3, load: '320 lb', rpe: 7, status: 'auto' },
      { reps: 3, load: '320 lb', rpe: 7, status: 'auto' },
      { reps: 3, load: '320 lb', rpe: 7, status: 'manual' },
    ] },
    { name: 'Barbell Overhead Press', sets: [
      { reps: 8, load: '115 lb', rpe: 6, status: 'auto' },
      { reps: 8, load: '115 lb', rpe: 6, status: 'auto' },
      { reps: 8, load: '115 lb', rpe: 7, status: 'auto' },
    ] },
    { name: 'Pin Good Morning', sets: [
      { reps: 10, load: '155 lb', rpe: 6, status: 'auto' },
      { reps: 10, load: '155 lb', rpe: 6, status: 'auto' },
    ] },
    { name: 'Chest-Supported Row', sets: [
      { reps: 9, load: '90 lb', rpe: 9, status: 'auto' },
      { reps: 9, load: '90 lb', rpe: 9, status: 'auto' },
      { reps: 8, load: '90 lb', rpe: 9, status: 'auto' },
      { reps: 8, load: '90 lb', rpe: 9, status: 'auto' },
    ] },
  ],
};
