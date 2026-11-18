// Preloaded (node --import) by tests/browser_process.py into every Node browser test.
// Browser tests must not depend on the public internet. Every page loads Google Fonts and jsDelivr CSS, and the tests
// wait for the page "load" event, so a slow or stalled network on the Mac made a walk stall about 300 s or run to its
// 600/900 s limit (ai4-105304 and ai5-172241, 17 Nov 2026) while the same commit passed in other runs.
// This makes every host except the local one fail to resolve at once. Nothing is changed in the app or in the pinned
// release helpers. If Playwright is not installed here (a non-browser Node test), this does nothing.
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// --no-proxy-server: a system proxy would resolve names itself and bypass the resolver rule.
export const HERMETIC_CHROME_ARGS = ["--no-proxy-server", "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost"];
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
try {
  const pw = await import(pathToFileURL(path.join(repo, "calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs")).href);
  const type = pw.chromium;
  if (!type.__hermetic) {
    const launch = type.launch.bind(type);
    type.launch = (options = {}) => launch({ ...options, args: [...(options.args || []), ...HERMETIC_CHROME_ARGS] });
    type.__hermetic = true;
  }
} catch (_error) { /* Playwright is not installed: not a browser test */ }
