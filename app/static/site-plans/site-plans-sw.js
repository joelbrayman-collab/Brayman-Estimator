/* Site Plans service worker (Joel, 23 Oct 2026). Scope /site-plans/ only: CalibraytAI Field keeps /field-sw.js
   (scope "/") and its own cache, untouched. Served at /site-plans/sw.js (app/routes/site_plans.py).

   Only Site Plans pages, plan files and this app's own static files are kept, always network first: with signal
   the phone gets the current plan from CalibraytAI; without signal it gets the copy it already has (marked
   "offline"). Nothing else is ever stored: no office page, no sign-in page, no redirect. The page script keeps a
   plan when it is opened or saved; signing out, and every sign-in page, deletes this cache. */
var CACHE = "calibrayt-site-plans-v1";
var PREFIX = "calibrayt-site-plans";
var SHELL = [
  "/static/site-plans/site-plans.css?v=1",
  "/static/site-plans/site-plans.js?v=1",
  "/static/site-plans/site-plans-icon-180.png",
  "/static/site-plans/site-plans-icon-32.png",
  "/static/site-plans/manifest.webmanifest",
];

function isPlansPath(pathname) {
  return (
    pathname === "/site-plans/" ||
    /^\/site-plans\/projects\/\d+$/.test(pathname) ||
    /^\/site-plans\/projects\/\d+\/(plan|drawing)\/\d+$/.test(pathname) ||
    /^\/site-plans\/projects\/\d+\/(plan|drawing)\/\d+\.pdf$/.test(pathname) ||
    /^\/site-plans\/projects\/\d+\/(plan|drawing)\/\d+\/page-\d+\.pdf$/.test(pathname)
  );
}

function isShell(pathname) {
  return pathname.indexOf("/static/site-plans/") === 0;
}

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(SHELL);
    }).catch(function () {}).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  // Only this app's older caches are removed; Field's cache is never touched.
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (key) {
        return key.indexOf(PREFIX) === 0 && key !== CACHE;
      }).map(function (key) {
        return caches.delete(key);
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

function markOfflineCopy(response) {
  if (!response) return response;
  var type = response.headers.get("Content-Type") || "";
  if (type.indexOf("text/html") === -1) return response;
  return response.text().then(function (html) {
    return new Response(html.replace('data-sp-copy="live"', 'data-sp-copy="offline"'), {
      status: 200,
      headers: { "Content-Type": type },
    });
  });
}

var NOT_SAVED =
  '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
  '<title>No signal | Site Plans</title></head><body style="font:17px -apple-system,sans-serif;margin:24px;color:#14202e">' +
  '<h1 style="font-size:24px">No signal</h1><p>This page is not saved on this phone. Plans you opened before, or saved ' +
  'with Save for offline, open without signal.</p><p><a href="/site-plans/">Back to Site Plans</a></p></body></html>';

function networkFirst(request) {
  return fetch(request)
    .then(function (response) {
      var finalPath = "";
      try { finalPath = new URL(response.url).pathname; } catch (err) { finalPath = ""; }
      if (response && response.status === 200 && !response.redirected && (isPlansPath(finalPath) || isShell(finalPath))) {
        var copy = response.clone();
        caches.open(CACHE).then(function (cache) { return cache.put(request, copy); }).catch(function () {});
      }
      return response;
    })
    .catch(function () {
      return caches.match(request, { ignoreSearch: !isShell(new URL(request.url).pathname) }).then(function (cached) {
        if (cached) return markOfflineCopy(cached);
        if (request.mode === "navigate") {
          return new Response(NOT_SAVED, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } });
        }
        return new Response("", { status: 504, statusText: "Offline" });
      });
    });
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;
  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (!isPlansPath(url.pathname) && !isShell(url.pathname)) return;  // sign-in, sign-out, sw.js: network only
  event.respondWith(networkFirst(request));
});

self.addEventListener("message", function (event) {
  if (!event.data || event.data.type !== "clear-site-plans-cache") return;
  event.waitUntil(
    caches.delete(CACHE).then(function () {
      if (event.source) event.source.postMessage({ type: "site-plans-cache-cleared" });
    })
  );
});
