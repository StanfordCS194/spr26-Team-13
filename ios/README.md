# iOS prototype

iPhone-side of TrainAR. The add-program flow is wired to the same Flask ingestion
API used by the desktop demo.

## Run with backend parsing

From the repo root:

```bash
python -m src.main --demo --host 127.0.0.1 --port 5001
```

Then open:

```text
http://127.0.0.1:5001/ios/
```

The iOS page posts selected files to `/api/programs/parse`. If you open
`ios/index.html` directly from disk, the page falls back to
`http://127.0.0.1:5001/api/programs/parse`.

React + Babel are loaded from a CDN at the top of the HTML. No build step.

## Supabase backend

The iOS app now uses Supabase for production auth and data. `index.html` loads:

- `supabase.js` — browser-safe Supabase client config
- `auth.js` — Supabase Auth adapter for `useAuth()`
- `data.js` — program/session/profile data adapter

The database schema lives in `../supabase/migrations/` and has RLS enabled on
all public tables. Saved programs are written as:

- `programs`
- `program_days`
- `program_blocks`
- `program_exercises`

Workout history is stored in:

- `workout_sessions`
- `workout_exercise_logs`
- `workout_sets`
- `personal_records`

## Layout

- `index.html` — entry point, pulls in scripts in dependency order
- `tokens.css` — design tokens (dark theme, lime accent)
- `ui.jsx` — shared primitives (Icon, Button, Card, Input)
- `ios-frame.jsx` — iPhone device frame (status bar, dynamic island, home indicator)
- `screens-signup.jsx` — splash, auth, name screens
- `auth.js` — `useAuth()` stub — swap with real backend later
- `ingestion.js` — upload adapter for the Flask parser API
- `app.jsx` — wires the screens into the device frame
