# CalibraytAI training site

The Training & Acceptance Centre runs on its own Render service with its own database. It is never
switched on in the production office: there, every `/training` page answers 404 and the training
company cannot be built (the command refuses).

## What it is

- The same CalibraytAI code as production (branch `main`, so the lessons match the released version),
  with `TRAINING_ENVIRONMENT=1`.
- Its own disk and SQLite database: synthetic training records only. Nothing on it touches real
  customers, suppliers or money, and production never reads it.
- Every page shows a "Training site · synthetic records only" bar with a link to the Training Centre.
- Ben and Darcy each get a training sign-in. Contractor people sign in on the office sign-in page,
  supplier people on the supplier sign-in page; both return to `/training`.

## Setting it up (needs Joel's authorization: a new paid service)

1. Render → New → Web Service, repository `joelbrayman-collab/Brayman-Estimator`, branch `main`,
   same region (Virginia), runtime Python.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 1 --bind 0.0.0.0:$PORT 'app:create_app()'`
   - Plan: the same as the office (Starter). Auto-deploy: off.
   - Disk: 1 GB mounted at `/opt/render/project/src/instance`.
   - Name: `calibraytai-training`.
2. Environment variables: `TRAINING_ENVIRONMENT=1`, a new random `SECRET_KEY` (not the office's),
   `CALIBRAYTAI_HOSTED=1`. No production credentials, no outgoing mail provider (training sign-ins are
   handed over directly).
3. Deploy, then in the service Shell:
   `flask db upgrade` and `flask training build-environment`.
   The command prints each training person's email and a one-time password. Give Ben and Darcy theirs
   privately; they change it in the first lesson.
4. Check: `/training/signin` opens; signing in as Ben shows the contractor modules; as Darcy the supplier
   modules; the production office still answers 404 at `/training`.

## Keeping it in step with releases

Deploy the training site after each production release, from the same commit. The lessons' screenshots
are retaken by `tools/training/capture_contractor_shots.mjs` and `capture_supplier_shots.mjs` on the
release candidate, and the release gate's browser checks include the Training Centre walk
(`tools/release/evidence_training.mjs`).

## Resetting the training company

Training records and practice work stay until the database is replaced. To start a fresh cohort:
stop the service, move the old database aside on the disk, deploy, then `flask db upgrade` and
`flask training build-environment` again.
