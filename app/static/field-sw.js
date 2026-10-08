/* Field shell only. Office, estimating, pricing, suppliers, contracts, and QuickBooks are not cached. */
var CACHE = "calibrayt-field-shell-v1";
var PRECACHE = [
  "/static/js/field.js",
  "/static/js/contextual_help.js",
  "/static/css/field.css",
  "/static/manifest.webmanifest",
  "/static/branding/calibrayt-home-icon-180.png",
];

function isFieldDocument(pathname) {
  if (pathname === "/field" || pathname === "/field/" || pathname === "/field/today") {
    return true;
  }
  if (pathname === "/field/projects") {
    return true;
  }
  if (/^\/field\/projects\/\d+$/.test(pathname)) {
    return true;
  }
  if (/^\/field\/projects\/\d+\/capture$/.test(pathname)) {
    return true;
  }
  return false;
}

function isFieldAsset(pathname) {
  return (
    pathname === "/static/js/field.js" ||
    pathname === "/static/js/contextual_help.js" ||
    pathname === "/static/css/field.css" ||
    pathname === "/static/manifest.webmanifest" ||
    pathname === "/static/branding/calibrayt-home-icon-180.png"
  );
}

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches
      .open(CACHE)
      .then(function (cache) {
        return cache.addAll(PRECACHE);
      })
      .then(function () {
        return self.skipWaiting();
      })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (keys) {
        return Promise.all(
          keys
            .filter(function (key) {
              return key !== CACHE;
            })
            .map(function (key) {
              return caches.delete(key);
            })
        );
      })
      .then(function () {
        return self.clients.claim();
      })
  );
});

function networkFirst(request) {
  return fetch(request)
    .then(function (response) {
      var finalPath = "";
      try {
        finalPath = new URL(response.url).pathname;
      } catch (err) {
        finalPath = "";
      }
      var cacheable =
        response &&
        response.ok &&
        !response.redirected &&
        (isFieldDocument(finalPath) || isFieldAsset(finalPath));
      if (cacheable) {
        var copy = response.clone();
        caches.open(CACHE).then(function (cache) {
          cache.put(request, copy);
        }).catch(function () {});
      }
      return response;
    })
    .catch(function () {
      return caches.match(request, { ignoreSearch: true }).then(function (cached) {
        if (cached) {
          return cached;
        }
        if (request.mode === "navigate") {
          return caches.match("/field/today", { ignoreSearch: true });
        }
        return new Response("", { status: 504, statusText: "Offline" });
      });
    });
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") {
    return;
  }
  var url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }
  if (!isFieldDocument(url.pathname) && !isFieldAsset(url.pathname)) {
    return;
  }
  event.respondWith(networkFirst(request));
});

self.addEventListener("message", function (event) {
  if (!event.data || event.data.type !== "clear-field-cache") {
    return;
  }
  event.waitUntil(
    caches.delete(CACHE).then(function () {
      if (event.source) {
        event.source.postMessage({ type: "field-cache-cleared" });
      }
    })
  );
});
