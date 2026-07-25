# The Estimator

Construction estimating and commercial operations platform (Brayman Estimator).

## Start here

1. [`AGENTS.md`](AGENTS.md) — rules for AI agents
2. [`docs/README.md`](docs/README.md) — documentation index and reading order
3. [`docs/current-state.md`](docs/current-state.md) — factual repo snapshot
4. [`docs/session-handoff.md`](docs/session-handoff.md) — resume after a pause

## Run locally

```bash
# Cursor Terminal
source venv/bin/activate
export FLASK_APP=app.py
flask run
# or: python app.py
```

## Tests

```bash
./venv/bin/python -m pytest -q
```

## Governance

Platform governance, architecture principles, Feature Gate, and definition of done live under [`docs/`](docs/).
