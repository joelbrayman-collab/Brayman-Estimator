// Shared setup for the release browser evidence (Node Playwright from the locked
// concrete-slab package, Chrome channel; the repository's supported browser test environment).
import net from "node:net";
import path from "node:path";
import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";

export const REPO = process.env.EVIDENCE_REPO;
if (!REPO) throw new Error("EVIDENCE_REPO is required");
const pw = await import(pathToFileURL(path.join(REPO, "calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs")).href);
export const chromium = pw.chromium;
export function launch() {
  // The Mac uses Google Chrome. EVIDENCE_EXECUTABLE lets a workspace without Chrome use Chromium.
  const exe = process.env.EVIDENCE_EXECUTABLE;
  return chromium.launch(exe ? { executablePath: exe, headless: true } : { channel: "chrome", headless: true });
}
export function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close((e) => (e ? reject(e) : resolve(p))); });
  });
}
export function startOffice(port) {
  const child = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/concrete_page_server.py")], {
    cwd: REPO, env: { ...process.env, CONCRETE_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  child.stdout.on("data", (c) => (out += c)); child.stderr.on("data", (c) => (out += c));
  const ready = new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 30000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (child.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 50);
    };
    poll();
  });
  return { child, ready };
}
