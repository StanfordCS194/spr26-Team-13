# Team 13 Project

Link to wiki: https://github.com/StanfordCS194/spr26-Team-13/wiki

This repo is now scaffolded around shared contracts so the team can work in
parallel without drifting on schemas.

## First docs to read

- `docs/team-plan.md`
- `docs/api-contracts.md`
- `docs/architecture.md`

## Recommended setup

Use either `venv` or Conda. The project source of truth is `pyproject.toml`.

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

## Run the starter app

```bash
python src/main.py
```

## Run tests

```bash
pytest
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
- `tests/fixtures/`: example payloads for team-wide testing
