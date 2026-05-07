// Placeholder parsed-program payload.
//
// The review screen reads from window.PARSED_PROGRAM. Right now this is hard-
// coded sample data — when the backend ships, it can populate this object (or
// pass it as a prop) with the actual OCR/parser output.
//
// Shape is intentionally simple: title, author, totals, weekly schedule,
// flagged-for-review entries.

window.PARSED_PROGRAM = {
  title: 'Powerbuilding 5×',
  author: 'J. Nippard',
  description: 'We extracted 10 weeks · 5 days/week · 47 unique exercises. Review below before saving.',
  stats: [
    { label: 'Weeks',   value: '10' },
    { label: 'Days/wk', value: '5'  },
    { label: 'Lifts',   value: '47' },
  ],
  schedule: [
    { day: 'Mon', name: 'Full Body 1', tag: 'Squat focus' },
    { day: 'Tue', name: 'Full Body 2', tag: 'Bench focus' },
    { day: 'Wed', name: 'Full Body 3', tag: 'Pull focus' },
    { day: 'Thu', name: 'Rest',        tag: 'Recovery' },
    { day: 'Fri', name: 'Full Body 4', tag: 'Deadlift focus' },
    { day: 'Sat', name: 'Full Body 5', tag: 'Press / arms' },
    { day: 'Sun', name: 'Rest',        tag: 'Recovery' },
  ],
  flagged: [
    { exercise: 'Pin Good Morning',     issue: "Couldn't read pin height — defaulted to \"high\"." },
    { exercise: 'AMRAP test (week 10)', issue: 'Two options found — A and B. Pick one before week 10.' },
  ],
};

// Lines shown on the camera "paper" placeholder + the parsing screen's preview
// thumb. Mirrors what a typical strength program sheet looks like so the
// silhouette feels real.
window.PROGRAM_SAMPLE_LINES = [
  'Back Squat (Top Single) · 1×1 @ 87.5%',
  'Back Squat · 5×3 @ 77.5%',
  'OHP · 3×8',
  'Pin Good Morning · 2×8-10',
  'Chest-Sup. Row · 4×8-10',
  'Hanging Leg Raise · 3×10',
];
