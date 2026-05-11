# Voice coach: manual verification

This branch wires the voice coach end-to-end in iPhone mode (no Meta DAT SDK,
no glasses). The acceptance bar is: **say "log a set: 5 reps at 135 on bench"
into the native app and see that set appear in the History tab.**

## One-time setup

1. Create a Supabase access token in `.env`:

   ```env
   SUPABASE_URL=https://rcmlbgjqwpfzpiownxfy.supabase.co
   SUPABASE_ANON_KEY=<anon key, same one ios/supabase.js embeds>
   ```

   Use the same project the iOS web app already points at
   (`ios/supabase.js:5-6`). The anon key is safe to put in `.env` — RLS keeps
   writes scoped to `auth.uid()`.

2. Install Python deps:

   ```bash
   pip install -e .
   ```

   (`supabase` and `PyJWT` are now in `pyproject.toml`.)

3. Open `native-ios/TrainAR/TrainAR.xcodeproj` in Xcode at least once so the
   simulator/device is provisioned with your dev team.

## Running the demo

```bash
# Terminal 1 — backend (also serves the iOS web app at /ios/)
python -m src.main --demo --host 0.0.0.0 --port 5002
```

In Xcode, run TrainAR on a simulator. The default
`Info.plist:TRAINAR_WEB_URL` is `http://127.0.0.1:5002/ios/`. If you're
testing on a physical iPhone over Wi-Fi, change that key in the project
settings to your Mac's `:5002/ios/` URL.

1. Sign in to your Supabase account in the web view (same flow as before).
2. On the Train tab you should now see a green floating mic button at the
   bottom right.
3. Tap it. The app will prompt for mic + speech recognition access the first
   time.
4. Say: **"log a set: 5 reps at 135 on bench"**
5. The coach should speak back "Logged 5 reps of bench press at 135 pounds."
6. Switch to the History tab and confirm today's session shows bench press
   5 × 135.
7. In Supabase Studio, open `workout_sessions`, `workout_exercise_logs`, and
   `workout_sets` — there should be one new row in each, all tied to your
   `auth.uid()`.

## What the loop does, file-by-file

| Step | File | Function |
|---|---|---|
| 1. Mic tap | [ios/screens-main.jsx](../ios/screens-main.jsx) | `CoachMicFab` sends `startListening` to native |
| 2. Speech → transcript | [native-ios/TrainAR/TrainAR/AppleVoiceBridge.swift](../native-ios/TrainAR/TrainAR/AppleVoiceBridge.swift) | `startListening()` runs `SFSpeechRecognizer`, emits `voiceCommand` |
| 3. Transcript → coach | [ios/app.jsx](../ios/app.jsx) | `onGlassesEvent` calls `askTrainARCoach(transcript)` |
| 4. JWT-stamped POST | [ios/assistant.js](../ios/assistant.js) | Attaches `Bearer <supabase access token>` |
| 5. Flask route | [src/app/program_review/web_demo.py](../src/app/program_review/web_demo.py) | `assistant_chat_api` parses JWT, builds Supabase client, threads context |
| 6. Tool dispatch | [src/assistant/service.py](../src/assistant/service.py) | `_execute_action` passes context into the tool |
| 7. Supabase write | [src/assistant/tools.py](../src/assistant/tools.py) | `log_set` creates session + exercise log + set under `auth.uid()` |
| 8. Spoken reply | [native-ios/TrainAR/TrainAR/AppleVoiceBridge.swift](../native-ios/TrainAR/TrainAR/AppleVoiceBridge.swift) | `speakResponse` → `AVSpeechSynthesizer` |
| 9. UI refresh | [ios/assistant.js](../ios/assistant.js) → [ios/app.jsx](../ios/app.jsx) | `trainar:history-changed` event re-runs `loadTrainarData` |

## Browser-only fallback

You don't need the native shell to demo the rest of the stack:

```bash
python -m src.main --demo --host 127.0.0.1 --port 5002
# open http://127.0.0.1:5002/ios/ in Safari/Chrome
```

The mic button falls back to a `prompt()` text box. Sign in, then type any
of the commands the assistant understands. The JWT forwarding + Supabase
writes work the same way.

## Known follow-ups (out of scope for this branch)

- Meta DAT SDK integration — glasses code paths are still mocked.
- A nicer in-app listening UI (waveform, "tap to stop").
- Surface tool errors (e.g. `supabase_error`) inline in the chat overlay.
- Wake-word ("hey trainar") instead of tap-to-talk.
