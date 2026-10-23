/* Site Plans (Joel, 23 Oct 2026): the viewer layout, offline copies and sign-out. No library.

   - Layout: computers and Android show the whole PDF in the browser's own viewer (an iframe). iPhone and iPad
     Safari shows only the first page of a PDF inside a page, so there each page is its own one-page PDF in an
     <img>, which Safari draws sharp at any zoom; pinch with two fingers to zoom.
   - Offline: the service worker (/site-plans/sw.js, scope /site-plans/ only) keeps what was opened; opening a plan
     also keeps all its pages; "Save for offline" keeps every plan of the project. All in one cache,
     calibrayt-site-plans-v1, on this phone only.
   - Sign out removes that cache first (the sign-in page removes it too, js/sign-in-clears-field-cache.js). */
(function () {
  "use strict";
  var CACHE = "calibrayt-site-plans-v1";
  var PREFIX = "calibrayt-site-plans";
  var body = document.body;

  function isAppleTouch() {
    var ua = navigator.userAgent || "";
    return /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }
  var pagesLayout = isAppleTouch() || /[?&]layout=pages\b/.test(location.search);

  if ("serviceWorker" in navigator) {
    try { navigator.serviceWorker.register("/site-plans/sw.js", { scope: "/site-plans/" }).catch(function () {}); }
    catch (e) { /* no offline copies on this browser */ }
  }

  if (body.getAttribute("data-sp-copy") === "offline") {
    var note = document.querySelector("[data-sp-offline-note]");
    if (note) note.hidden = false;
  }

  function hasCaches() { try { return "caches" in window; } catch (e) { return false; } }

  function keep(url) {
    // Fetch one address and keep the answer in this phone's Site Plans cache. Resolves true when kept.
    return fetch(url, { credentials: "same-origin" }).then(function (response) {
      if (!response.ok || response.redirected || response.status !== 200) return false;
      if (!hasCaches()) return true;  // the service worker keeps it, where there is one
      return caches.open(CACHE).then(function (cache) { return cache.put(url, response); }).then(function () { return true; });
    }).catch(function () { return false; });
  }

  function pageUrls(viewUrl, pages) {
    var out = [];
    for (var n = 1; n <= pages; n++) out.push(viewUrl + "/page-" + n + ".pdf");
    return out;
  }

  // Keep one plan: its viewer page and, for this phone's layout, its pages or its whole file.
  function keepPlan(viewUrl, wholeUrl, pages) {
    var urls = [viewUrl].concat(pagesLayout ? pageUrls(viewUrl, pages) : [wholeUrl]);
    var kept = 0;
    return urls.reduce(function (chain, url) {
      return chain.then(function () { return keep(url).then(function (ok) { if (ok) kept += 1; }); });
    }, Promise.resolve()).then(function () { return kept === urls.length; });
  }

  // The project list and a project's plans are kept as they are seen. Once the service worker controls the page it
  // keeps them itself; before that (the very first visit) the page keeps its own copy.
  var screen = body.getAttribute("data-sp-screen");
  if ((screen === "projects" || screen === "project") && body.getAttribute("data-sp-copy") === "live") {
    var controlled = navigator.serviceWorker && navigator.serviceWorker.controller;
    if (!controlled) keep(location.pathname);
  }

  // ------------------------------------------------------------------ viewer
  var viewer = document.querySelector("[data-sp-viewer]");
  if (viewer) {
    var whole = viewer.getAttribute("data-sp-whole");
    var pages = parseInt(viewer.getAttribute("data-sp-pages"), 10) || 0;
    var frame = viewer.querySelector("[data-sp-whole-frame] iframe");
    var list = viewer.querySelector("[data-sp-page-list]");
    if (pagesLayout && list) {
      body.setAttribute("data-sp-layout", "pages");
      list.hidden = false;
      Array.prototype.forEach.call(list.querySelectorAll("img[data-src]"), function (img) {
        img.addEventListener("error", function () {
          // This browser does not draw a PDF in an image: show the page in a frame instead.
          var f = document.createElement("iframe");
          f.src = img.getAttribute("data-src");
          f.title = img.alt;
          f.style.width = "100%";
          f.style.height = "70vh";
          img.replaceWith(f);
        }, { once: true });
        img.src = img.getAttribute("data-src");
      });
    } else {
      body.setAttribute("data-sp-layout", "whole");
      if (frame) frame.src = frame.getAttribute("data-src");
    }
    Array.prototype.forEach.call(viewer.querySelectorAll("[data-sp-goto]"), function (a) {
      a.addEventListener("click", function (event) {
        if (pagesLayout || !frame) return;  // the page list scrolls to the sheet by itself
        event.preventDefault();
        frame.src = whole + "#page=" + a.getAttribute("data-sp-goto") + "&view=FitH";
      });
    });
    if (navigator.standalone) {
      // In the Home Screen app a PDF opened on its own has no way back: keep the plan inside the app.
      var own = viewer.querySelector("[data-sp-open-file]");
      if (own) own.hidden = true;
    }
    // A plan that was opened stays on this phone, all its pages, for when there is no signal.
    if (body.getAttribute("data-sp-copy") === "live") {
      window.setTimeout(function () {
        keepPlan(location.pathname, whole, pages).then(function (done) {
          viewer.setAttribute("data-sp-kept", done ? "yes" : "no");
        });
      }, 400);
    }
  }

  // ------------------------------------------------------------------ project: saved badges and Save for offline
  var files = Array.prototype.slice.call(document.querySelectorAll("[data-sp-file]"));
  function primary(li) {
    var view = li.getAttribute("data-sp-view");
    return pagesLayout ? view + "/page-1.pdf" : li.getAttribute("data-sp-whole");
  }
  function markSaved() {
    if (!hasCaches()) return Promise.resolve(0);
    return caches.open(CACHE).then(function (cache) {
      return Promise.all(files.map(function (li) {
        return cache.match(primary(li), { ignoreSearch: true }).then(function (hit) {
          var badge = li.querySelector("[data-sp-saved]");
          if (badge) badge.hidden = !hit;
          return hit ? 1 : 0;
        });
      }));
    }).then(function (hits) { return hits.reduce(function (a, b) { return a + b; }, 0); }).catch(function () { return 0; });
  }
  if (files.length) markSaved();
  var save = document.querySelector("[data-sp-save]");
  var status = document.querySelector("[data-sp-save-status]");
  if (save) {
    save.addEventListener("click", function () {
      save.disabled = true;
      status.textContent = "Saving the plans on this phone…";
      var done = 0;
      files.reduce(function (chain, li) {
        return chain.then(function () {
          var view = li.getAttribute("data-sp-view");
          // The number of pages comes from the viewer page itself (the file is the authority).
          return fetch(view, { credentials: "same-origin" }).then(function (r) { return r.ok ? r.text() : ""; })
            .then(function (html) {
              var m = /data-sp-pages="(\d+)"/.exec(html || "");
              var n = m ? parseInt(m[1], 10) : parseInt(li.getAttribute("data-sp-pages"), 10) || 0;
              return keepPlan(view, li.getAttribute("data-sp-whole"), n);
            })
            .then(function (ok) { if (ok) done += 1; })
            .catch(function () {});
        });
      }, Promise.resolve()).then(function () {
        return keep(save.getAttribute("data-sp-project-url"));
      }).then(function () {
        return keep("/site-plans/");
      }).then(function () {
        return markSaved();
      }).then(function () {
        save.disabled = false;
        save.setAttribute("data-sp-saved-count", String(done));
        status.textContent = done === files.length
          ? "Saved " + done + " of " + files.length + " plans on this phone. They open without signal until you sign out."
          : "Saved " + done + " of " + files.length + " plans. Check the signal and tap Save for offline again.";
      });
    });
  }

  // ------------------------------------------------------------------ sign out removes this phone's copies
  var form = document.querySelector("[data-sp-sign-out-form]");
  if (form) {
    form.addEventListener("submit", function (event) {
      if (form.getAttribute("data-sp-cleared") === "yes" || !hasCaches()) return;
      event.preventDefault();
      var go = function () { form.setAttribute("data-sp-cleared", "yes"); form.submit(); };
      var timer = window.setTimeout(go, 1500);
      caches.keys().then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k.indexOf(PREFIX) === 0; })
          .map(function (k) { return caches.delete(k); }));
      }).catch(function () {}).then(function () { window.clearTimeout(timer); go(); });
    });
  }
})();
