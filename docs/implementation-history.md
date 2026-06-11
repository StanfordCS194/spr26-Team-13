# Implementation History

This file gives future teammates a repo-wide map from major implemented areas to
the PRs and commits that introduced them. It intentionally covers work from the
whole team. It is not a replacement for GitHub issues; use issues for open work
and this document for historical context.

## Foundation and Contracts

The repo was first organized around shared contracts and subsystem boundaries:
`src/contracts/`, `src/ingestion/`, `src/runtime/`, `src/sensing/`,
`src/glasses/`, `src/app/`, and `src/export/`.

Key references: `43fdb79`, `5e1c8ec`.

## Program Ingestion

The ingestion path converts uploaded workout files into canonical
`TrainingProgram` objects, preserving days, blocks, and exercises where the
source document provides them.

Key references: PR #34 / `784b326`, PR #42 / `16a9def`.

## Backend and App Data

The app backend stores programs, days, blocks, exercises, sessions, sets, and
personal records in Supabase. The browser iOS prototype reads and writes through
that data model.

Key references: PR #77 / `21fd2f0`, `752d8c7`.

## Frontend and Onboarding

The frontend work reshaped signup, training profile setup, program screens, and
coach-facing UI around the backend and assistant flows.

Key references: PR #87 / `bd77ff5`.

## Assistant and Workout Control

The assistant work connects natural-language commands to structured actions:
logging sets, starting or finishing workouts, querying PRs/history, generating
workouts, confirming off-current exercise logging, and producing personalized
coach replies.

Key references: PR #79 / `1675cdb`, `a1f8523`, `1ebc550`, `024854d`,
`3f41435`, `6712786`, `25be9c4`, PR #85 / `b7bd9e4`, `1cd08e0`, PR #91 /
`ba4fbdf`.

## Native iOS, Glasses, and HUD

The glasses/native work includes the OpenCV display demo, optional audio cues,
the Xcode shell, wake-word voice bridge, HUD prep, Ray-Ban/Meta DAT exploration,
and demo-safe camera fallbacks.

Key references: PR #33 / `368a48c`, `090b688`, `5184914`, `2e39a7d`, PR #80 /
`78bbd03`, `062b004`, `31450da`, `601642b`, PR #90 / `5a404ba`, `9895779`.

## Spreadsheet, History, and Seed Data

Spreadsheet and history work added Jeff Nippard-style spreadsheet reading,
write-back of logged weights, day-number handling, richer workout history, and
Supabase seed tooling for demos.

Key references: `6fb7900`, `1373da5`, `04b1db5`, `1d3d427`.

## Summaries, Progression, and Export

Training intelligence work added progression recommendations, estimated 1RMs,
post-workout summaries, PR detection, CSV exports, evidence-library expansion,
and integration coverage.

Key references: PR #86 / `110ec9b`, `a5bfca1`, `6350f5f`.

## Repository Hygiene and Demo Safety

Cleanup work removed local artifacts and oversized files, tightened demo login
safety, and kept shareable branches from carrying local-only bypasses.

Key references: `c181461`, `3a987ec`, `1f02ec7`, `91024a3`.

## Local Development Notes

- Browser iOS prototype: run `python -m src.main --demo --host 127.0.0.1 --port 5001`
  and open `http://127.0.0.1:5001/ios/`.
- Native iOS Simulator: run `python -m src.main --demo --host 127.0.0.1 --port 5002`.
- Physical iPhone from Xcode: run `python -m src.main --demo --host 0.0.0.0 --port 5002`,
  then update `TRAINAR_WEB_URL`, `ChatEndpointURL`, and
  `NSAppTransportSecurity` in `native-ios/TrainAR/TrainAR/Info.plist` to use
  your Mac's current LAN IP from `ipconfig getifaddr en0`.
