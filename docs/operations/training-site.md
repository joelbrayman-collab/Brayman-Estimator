# CalibraytAI training site

The Training & Acceptance Centre runs at https://training.calibraytai.com on the HostPapa VPS (service
`calibrayt-training`, code in `/opt/calibrayt/app`, database on the server's disk; installed by
`tools/hosting/install_training_centre.sh`, 22 Oct 2026), with its own database. It is never
switched on in the production office: there, every `/training` page answers 404 and the training
company cannot be built (the command refuses).

## Updating it to a release (23 Oct 2026)

`bash tools/hosting/install_training_centre.sh [commit]` as root in WHM Terminal. With no argument it runs the
v1rel8 release candidate named in the script. It checks out that pinned commit (not a branch head), stops the
service, takes a timestamped copy of `/opt/calibrayt/data/training.db` in `/opt/calibrayt/data/backups/` with
SQLite's backup, runs the migrations against that database, runs `flask training build-environment
--passwords-from-env` (adds only what is missing; never resets passwords, progress or acceptance results),
restarts, and checks over HTTPS that `/training/signin` answers 200 and shows the three choices (contractor,
crew (Field), supplier). `/opt/calibrayt/env` and the rest of `/opt/calibrayt/data` are not changed. To go back:
stop the service, copy the backup over `training.db`, and run the script with the earlier commit.

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

## Supplier practice login (training administrators, 24 Oct 2026)

Joel takes the Supplier trainee pathway from his own Owner training sign-in, so his Contractor and Field progress
and all acceptance results stay where they are (one trainee record, each pathway's lessons and tests kept apart by
key). One sign-in cannot be on the contractor and the supplier side at once, so the Supplier Hub practice uses a
separate synthetic login (`app/training/practice.py`):

- `flask training build-environment` adds, for each training administrator (the training company's Instance Owner
  and System Administrators), "<Name> (supplier practice)" at `supplier-practice-<user id>@training.calibraytai.invalid`:
  a member of BMR Winchester (training) only (the synthetic supplier), no contractor membership and no usable
  password, so it cannot sign in from any sign-in page. Running the command again adds nothing; it is printed as a
  `PRACTICE` line. Existing accounts print "(already existed; password unchanged)".
- The administrator chooses Supplier owner, Supplier administrator or PRO Desk in the header Pathway switch. On each
  Supplier Hub step of a supplier lesson, "Open the supplier practice site as <Name> (supplier practice)" (a
  CSRF-protected POST) checks again that he is a training administrator and that the login is his own, synthetic,
  supplier-only practice login, writes an audit line (`app.training.supplier_practice` in the application log) and
  opens the Supplier Hub page as that login. Every training-site page then shows "Back to the Training Centre as
  <Name>", which signs him back in as himself (same checks, audited) at the lesson step. The practice login never
  registers or records training; the Training Centre only offers it the way back.
- With `TRAINING_ENVIRONMENT` off nothing of this exists: the routes answer 404, the Supplier roles are not offered
  and the build refuses. No production permission or sign-in changed.

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
