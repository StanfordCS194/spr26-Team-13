# Implementation History

This file gives future teammates a quick map from major implemented areas to
the PRs and commits that introduced them. It is not a replacement for GitHub
issues; use issues for open work and this document for historical context.

## Foundation

- `43fdb79` Scaffold shared contracts and team repo structure
- `5e1c8ec` Add `__init__.py` to all subsystem packages

These commits established the project layout around shared contracts:
`src/contracts/`, `src/ingestion/`, `src/runtime/`, `src/sensing/`,
`src/glasses/`, `src/app/`, and `src/export/`.

## Program Ingestion

- PR #34, `784b326` Add Docling and Gemini workout ingestion flow
- PR #42, `16a9def` Improve block assignment and speed up Docling normalization

These commits added the document import pipeline that converts uploaded program
files into canonical `TrainingProgram` contracts.

## Backend and Supabase App Data

- PR #77, `21fd2f0` Add Supabase backend for iOS app
- PR #77, `752d8c7` Fix Supabase migration review issues

These commits added the Supabase-backed app data model for programs, days,
blocks, exercises, sessions, sets, and personal records.

## Assistant and Workout Control

- PR #79, `1675cdb` Add OpenAI assistant service for workout commands
- `25be9c4` Voice coach: add Supabase workout tools
- PR #85, `b7bd9e4` Fix voice workout flows and HUD prep
- PR #85, `1cd08e0` Add personalized evidence-backed coach onboarding

These commits connected natural-language commands to structured workout
actions, Supabase writes, off-current exercise confirmation, and personalized
coach behavior.

## Native iOS and Glasses

- PR #33, `368a48c` Implement glasses display demo overlay
- `2e39a7d` Add optional audio cues to workout demo
- PR #80, `78bbd03` Add native iOS shell and glasses coach bridge
- `601642b` Audio coach: exercise guidance layer + enriched next-set coaching reply

These commits introduced the display demo, audio cues, native Xcode shell, and
the bridge used by the iOS web app and glasses-related flows.

## Summaries, Progression, and Export

- PR #86, `110ec9b` Coach: progressive overload recommendations + smart post-workout summary
- PR #86, `a5bfca1` Add CSV export module and expand evidence library to 11 sources
- PR #86, `6350f5f` Tests: 25 integration tests for progression, post-workout summary, and CSV export

These commits added progression recommendations, post-workout summaries, PR
detection, CSV export endpoints, and integration coverage.

## Local Development Notes

- Browser iOS prototype: run `python -m src.main --demo --host 127.0.0.1 --port 5001`
  and open `http://127.0.0.1:5001/ios/`.
- Native iOS Simulator: run `python -m src.main --demo --host 127.0.0.1 --port 5002`.
- Physical iPhone from Xcode: run `python -m src.main --demo --host 0.0.0.0 --port 5002`,
  then update `TRAINAR_WEB_URL`, `ChatEndpointURL`, and
  `NSAppTransportSecurity` in `native-ios/TrainAR/TrainAR/Info.plist` to use
  your Mac's current LAN IP from `ipconfig getifaddr en0`.
