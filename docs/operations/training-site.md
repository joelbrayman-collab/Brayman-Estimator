# CalibraytAI training site

The Training & Acceptance Centre runs on its own Render service with its own database. It is never
switched on in the production office: there, every `/training` page answers 404 and the training
company cannot be built (the command refuses).

## What it is

- The same CalibraytAI code as production (branch `main`, so the lessons match the released version),
  with `TRAINING_ENVIRONMENT=1`.
- Its own disk and SQLite database: fictional training records only. Nothing on it touches real
  customers, suppliers or money, and production never reads it.
- Every page shows a "Training site · synthetic records only" bar with a link to the Training Centre.
- Ben and Darcy each get a training sign-in. Contractor people sign in on the office sign-in page,
  supplier people on the supplier sign-in page; both return to `/training`.
- Three trainings (22 Oct 2026), chosen on `/training/signin`: contractor owners and office staff
  (`app/training/contractor.py`), the Field crew on the iPhone ("I work on a crew (Field)",
  `app/training/field_crew.py`, eight modules) and supplier owners and PRO Desk staff
  (`app/training/supplier.py`). A Field-only person (Kevin, Liam) registers straight into the Field Crew
  training and sees nothing else; it is stored as the contractor pathway with role Field worker, so no
  schema change. The owner previews it at `/training/review/field-crew` and follows the crew's lessons
  and Field acceptance results (failing or blocked tests flagged) on `/training/admin`.

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
4. Check: `/training/signin` opens; signing in as Ben shows the contractor modules; as Kevin the eight
   Field Crew modules; as Darcy the supplier modules; the production office still answers 404 at `/training`.

## Keeping it in step with releases

Deploy the training site after each production release, from the same commit. The lessons' screenshots
are retaken by `tools/training/capture_contractor_shots.mjs`, `capture_field_crew_shots.mjs` (Field at
iPhone size, 390 x 844) and `capture_supplier_shots.mjs` on the release candidate, and the release gate's
browser checks include the Training Centre walks (`tools/release/evidence_training.mjs`,
`evidence_field_crew.mjs`).

## Resetting the training company

Training records and practice work stay until the database is replaced. To start a fresh cohort:
stop the service, move the old database aside on the disk, deploy, then `flask db upgrade` and
`flask training build-environment` again.
