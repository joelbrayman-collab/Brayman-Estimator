// Screenshots for the Guided Workflow Wizards lessons of the Training & Acceptance Centre (24 Oct 2026): contractor
// module 15 and supplier module 11 (app/training/wizards_lessons.py).
//
// Runs the wizards release walk (tools/release/evidence_wizards.mjs: the real pages on a local office built by the
// real migrations, synthetic data only) and keeps its pictures as app/static/training/shots/w-*.png (desktop
// 1280 x 900, phone 390 x 844). The walk fails on any server error or page error, so a lesson never shows a
// broken screen.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium node tools/training/capture_wizard_shots.mjs
import path from "node:path";
import { spawnSync } from "node:child_process";

const REPO = process.env.EVIDENCE_REPO;
if (!REPO) throw new Error("EVIDENCE_REPO is required");
const result = spawnSync("node", ["--test", "--test-concurrency=1", "--test-force-exit", "evidence_wizards.mjs"], {
  cwd: path.join(REPO, "tools/release"), stdio: "inherit",
  env: { ...process.env, WIZARD_SHOTS: path.join(REPO, "app/static/training/shots"), WIZARD_SHOT_PREFIX: "w-" },
});
process.exit(result.status ?? 1);
