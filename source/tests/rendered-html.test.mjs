import assert from "node:assert/strict";
import test from "node:test";

test("renders the Website's production metadata", async () => {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );

  assert.equal(response.status, 200);
  assert.match(
    response.headers.get("content-type") ?? "",
    /^text\/html\b/i,
  );
  const html = await response.text();
  assert.match(
    html,
    /<title>CalibraytAI — Construction Intelligence\. Calibrated\.<\/title>/,
  );
  assert.match(
    html,
    /<meta(?=[^>]*\bname=["']description["'])(?=[^>]*\bcontent=["']CalibraytAI connects the complete construction lifecycle through one authoritative project record\.["'])[^>]*>/i,
  );
  assert.match(html, /<link(?=[^>]*\brel=["']icon["'])(?=[^>]*\bhref=["']\/favicon\.svg["'])[^>]*>/i);
  assert.doesNotMatch(html, /\bname=["']codex-preview["']/i);
});
