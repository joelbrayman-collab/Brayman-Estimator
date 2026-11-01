// Task-First UX (31 Oct 2026): the Project page (/projects/<id>) keeps each part of the job in a closed section, and
// More actions closed. Before a walk reads or uses something on it, it opens them, as a person opens the section
// they need. Kept apart from evidence_common.mjs, whose bytes are pinned (tests/test_release_tools.py).
export const PROJECT_PAGE = /^\/projects\/\d+\/?$/;
export async function openSections(pg) {
  await pg.evaluate(() => document.querySelectorAll("details[data-ts-section], details[data-more-actions]")
    .forEach((d) => { d.open = true; }));
}
export async function openSectionsIfProjectPage(pg) {
  if (PROJECT_PAGE.test(new URL(pg.url()).pathname)) await openSections(pg);
}

// Task-First UX, Slice C (1 Nov 2026): the contractor wizards' start now opens the Guided Task and starts nothing.
// A run started before the retirement keeps working, so a walk that checks the runner opens such a run: made in the
// walk's own temporary database by tests/wizard_run_seed.py (the same service the start used). Returns the run id.
import { execFile } from "node:child_process";
import path from "node:path";
export function seedWizardRun(repo, databaseUri, key, email, projectId = "") {
  return new Promise((resolve, reject) => {
    execFile(path.join(repo, "venv/bin/python"), [path.join(repo, "tests/wizard_run_seed.py"), databaseUri, key, email,
      projectId ? String(projectId) : ""], { cwd: repo }, (err, stdout, stderr) => {
      const m = /RUN (\d+)/.exec(stdout || "");
      if (err || !m) return reject(new Error(`wizard run seed failed: ${err || ""}\n${stdout}\n${stderr}`));
      resolve(Number(m[1]));
    });
  });
}

// Field Today (Slice C, 1 Nov 2026): the job's secondary buttons, print and help are under a closed "More for today".
// A walk that uses one of them opens it first, as the crew member does.
export async function openFieldTodayMore(pg) {
  await pg.evaluate(() => document.querySelectorAll("details[data-field-today-more]").forEach((d) => { d.open = true; }));
}

// Set Up This Project (Slice C): the project settings and the "rural lot / address as written" field are in closed
// sections. A walk that fills them opens every section of the form first, as a person does.
export async function openSetUpSections(pg) {
  await pg.evaluate(() => document.querySelectorAll("[data-set-up-form] details").forEach((d) => { d.open = true; }));
}
