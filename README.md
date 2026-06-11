# Team 13 Project

Link to wiki: https://github.com/StanfordCS194/spr26-Team-13/wiki

This repo is now scaffolded around shared contracts so the team can work in
parallel without drifting on schemas.

## First docs to read

- `docs/team-plan.md`
- `docs/api-contracts.md`
- `docs/architecture.md`
- `docs/implementation-history.md`
- `ios/README.md` for the browser iOS prototype
- `native-ios/README.md` for the Xcode/native iOS shell

## Recommended setup

First, clone the repository and navigate into it:

```bash
git clone https://github.com/StanfordCS194/spr26-Team-13.git
cd spr26-Team-13
```

All subsequent commands should be run from this repository root. Use either `venv` or Conda. The project source of truth is `pyproject.toml`.

### Option 1: venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Conda

```bash
conda create -n team13 python=3.11
conda activate team13
pip install -r requirements.txt
```

## Run the local app

The Flask demo server powers the desktop review flow, iOS browser prototype,
coach chat routes, and native iOS shell during local development.

For the browser/iOS prototype parser flow:

```bash
python -m src.main --demo --host 127.0.0.1 --port 5001
```

Then open `http://127.0.0.1:5001/ios/`.

For the native Xcode shell on the iOS Simulator:

```bash
python -m src.main --demo --host 127.0.0.1 --port 5002
```

For a physical iPhone, run the server with `--host 0.0.0.0` and update the
LAN IP in `native-ios/TrainAR/TrainAR/Info.plist` before launching from Xcode.
See `native-ios/README.md` for the exact `TRAINAR_WEB_URL`, `ChatEndpointURL`,
and `NSAppTransportSecurity` steps.

## Run tests

```bash
python -m pytest
```

## Environment variables

Copy the example environment file before adding secrets:

```bash
cp .env.example .env
```

Do not commit `.env`.

## Repo map

- `src/contracts/`: shared schemas
- `src/shared/`: shared constants and validators
- `src/ingestion/`: import and program parsing
- `src/runtime/`: live workout state
- `src/sensing/`: rep detection and sensor adapters
- `src/glasses/`: display demo, audio, controls
- `src/app/`: summary, history, review flows
- `src/export/`: external logging/export
- `ios/`: browser-based iOS prototype
- `native-ios/`: Xcode shell wrapping the web app and native bridges
- `tests/fixtures/`: example payloads for team-wide testing

## Documentation expectations

- Keep feature behavior documented near the subsystem README.
- Use PR descriptions and `docs/implementation-history.md` for historical
  commit/PR context instead of creating retroactive issues for already-merged
  work.
- Use GitHub issues for active bugs, follow-ups, or remaining implementation
  tasks.

Charlie Abowd
