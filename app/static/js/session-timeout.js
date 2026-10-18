// Inactivity sign-out warning (Joel, 18 Oct 2026). The server signs an office or supplier
// account out after 30 minutes without activity (app/services/session_timeout.py). This page
// script warns shortly before, lets the person stay signed in, counts typing and tapping as
// activity, and keeps what was typed in a form if the time runs out, so it can be put back
// after signing in again. Drafts live in this tab's sessionStorage only and are restored only
// for the same person on the same page.
(function () {
  "use strict";
  var script = document.currentScript;
  if (!script || !window.fetch) return;
  var cfg = {
    timeout: Number(script.dataset.timeout) || 1800,
    warning: Number(script.dataset.warning) || 120,
    status: script.dataset.statusUrl,
    keepalive: script.dataset.keepaliveUrl,
    login: script.dataset.loginUrl,
    user: script.dataset.user || "",
  };
  var DRAFT_KEY = "calibraytai:draft:" + location.pathname;
  var DRAFT_MAX_AGE_MS = 2 * 60 * 60 * 1000;
  // Typing or tapping refreshes the server at most this often (5 minutes at the real limit).
  var ACTIVITY_PING_MS = Math.min(300, cfg.timeout / 6) * 1000;
  var deadline = Date.now() + cfg.timeout * 1000;
  var lastPing = Date.now();
  var checkTimer = null;
  var tickTimer = null;
  var panel = null;
  var expiring = false;

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  function schedule(ms) {
    clearTimeout(checkTimer);
    var wait = typeof ms === "number" ? ms : Math.max(0, deadline - cfg.warning * 1000 - Date.now());
    checkTimer = setTimeout(check, wait);
  }

  function readStatus() {
    return fetch(cfg.status, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
    })
      .then(function (response) { return response.json(); })
      .catch(function () { return null; });
  }

  function check() {
    readStatus().then(function (state) {
      if (!state) {
        // Offline or unreachable (Field pages work offline): do not sign out from here; the
        // server decides on the next request. Look again in a minute.
        schedule(60 * 1000);
        return;
      }
      if (!state.signed_in) { expire(); return; }
      deadline = Date.now() + state.remaining * 1000;
      if (state.remaining > cfg.warning) { hideWarning(); schedule(); return; }
      if (state.remaining <= 0) { expire(); return; }
      showWarning();
    });
  }

  function format(seconds) {
    var s = Math.max(0, Math.ceil(seconds));
    var m = Math.floor(s / 60);
    var r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  function buildPanel() {
    panel = document.createElement("div");
    panel.className = "session-timeout";
    panel.setAttribute("role", "alertdialog");
    panel.setAttribute("aria-live", "assertive");
    panel.setAttribute("aria-labelledby", "session-timeout-title");
    panel.setAttribute("aria-describedby", "session-timeout-text");
    panel.dataset.sessionTimeout = "warning";
    panel.hidden = true;
    panel.innerHTML =
      '<p class="session-timeout-title" id="session-timeout-title">Still there?</p>' +
      '<p class="session-timeout-text" id="session-timeout-text">For security you will be signed out in ' +
      '<strong class="session-timeout-clock">' + format(cfg.warning) + "</strong>" +
      " because there has been no activity. Anything you have typed will be kept.</p>" +
      '<button type="button" class="button session-timeout-stay">Stay signed in</button>';
    panel.querySelector(".session-timeout-stay").addEventListener("click", function () {
      keepalive();
    });
    document.body.appendChild(panel);
  }

  function showWarning() {
    if (!panel) buildPanel();
    var wasHidden = panel.hidden;
    panel.hidden = false;
    clearInterval(tickTimer);
    var tick = function () {
      var left = (deadline - Date.now()) / 1000;
      panel.querySelector(".session-timeout-clock").textContent = format(left);
      if (left <= 0) {
        clearInterval(tickTimer);
        // Another tab may have kept the session going: ask before signing out.
        readStatus().then(function (state) {
          if (state && state.signed_in && state.remaining > 0) {
            // Another tab kept the session going, or the server has a moment left.
            deadline = Date.now() + state.remaining * 1000;
            if (state.remaining > cfg.warning) { hideWarning(); schedule(); } else { showWarning(); }
          } else if (state) {
            expire();
          } else {
            schedule(60 * 1000);
          }
        });
      }
    };
    tick();
    tickTimer = setInterval(tick, 1000);
    if (wasHidden) panel.querySelector(".session-timeout-stay").focus({ preventScroll: true });
  }

  function hideWarning() {
    clearInterval(tickTimer);
    if (panel) panel.hidden = true;
  }

  function keepalive() {
    lastPing = Date.now();
    return fetch(cfg.keepalive, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json", "X-CSRFToken": csrfToken() },
    })
      .then(function (response) {
        if (response.status === 401) { expire(); return null; }
        return response.ok ? response.json() : null;
      })
      .then(function (state) {
        if (!state) return;
        deadline = Date.now() + state.remaining * 1000;
        hideWarning();
        schedule();
      })
      .catch(function () { /* offline: the next check decides */ });
  }

  function onActivity() {
    if (expiring || (panel && !panel.hidden)) return;
    if (Date.now() - lastPing >= ACTIVITY_PING_MS) keepalive();
  }

  function fieldsOf(form) {
    var saved = [];
    Array.prototype.forEach.call(form.elements, function (field) {
      if (!field.name || field.disabled || field.name === "csrf_token") return;
      var type = (field.type || "").toLowerCase();
      if (["password", "hidden", "file", "submit", "button", "reset", "image"].indexOf(type) !== -1) return;
      if (type === "checkbox" || type === "radio") {
        if (field.checked !== field.defaultChecked) saved.push({ name: field.name, value: field.value, checked: field.checked });
        return;
      }
      if (field.tagName === "SELECT") {
        var changed = Array.prototype.some.call(field.options, function (o) { return o.selected !== o.defaultSelected; });
        if (changed) saved.push({ name: field.name, value: field.value });
        return;
      }
      if (field.value !== field.defaultValue) saved.push({ name: field.name, value: field.value });
    });
    return saved;
  }

  function saveDraft() {
    var forms = [];
    Array.prototype.forEach.call(document.forms, function (form, index) {
      if ((form.getAttribute("method") || "get").toLowerCase() !== "post") return;
      var fields = fieldsOf(form);
      if (fields.length) forms.push({ index: index, action: form.getAttribute("action") || "", fields: fields });
    });
    if (!forms.length) return;
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ user: cfg.user, at: Date.now(), forms: forms }));
    } catch (e) { /* storage unavailable: nothing to keep */ }
  }

  function restoreDraft() {
    var raw = null;
    try {
      raw = sessionStorage.getItem(DRAFT_KEY);
      sessionStorage.removeItem(DRAFT_KEY);
    } catch (e) { return; }
    if (!raw) return;
    var draft;
    try { draft = JSON.parse(raw); } catch (e) { return; }
    if (!draft || draft.user !== cfg.user || Date.now() - draft.at > DRAFT_MAX_AGE_MS) return;
    var restored = 0;
    (draft.forms || []).forEach(function (saved) {
      var form = document.forms[saved.index];
      if (!form || (form.getAttribute("action") || "") !== saved.action) return;
      saved.fields.forEach(function (entry) {
        var named = form.elements.namedItem(entry.name);
        if (!named) return;
        var list = named.length !== undefined && !named.tagName ? Array.prototype.slice.call(named) : [named];
        list.forEach(function (field) {
          var type = (field.type || "").toLowerCase();
          if (type === "checkbox" || type === "radio") {
            if (field.value === entry.value) { field.checked = entry.checked; restored += 1; }
          } else if (list.length === 1) {
            field.value = entry.value;
            restored += 1;
          }
          field.dispatchEvent(new Event("input", { bubbles: true }));
        });
      });
    });
    if (!restored) return;
    var note = document.createElement("div");
    note.className = "session-timeout-restored";
    note.setAttribute("role", "status");
    note.dataset.sessionTimeout = "restored";
    note.innerHTML =
      "<span>We put back what you had typed before you were signed out. Check it, then save.</span>" +
      '<button type="button" class="button-secondary">OK</button>';
    note.querySelector("button").addEventListener("click", function () { note.remove(); });
    document.body.appendChild(note);
  }

  function expire() {
    if (expiring) return;
    expiring = true;
    hideWarning();
    saveDraft();
    var next = location.pathname + location.search;
    var join = cfg.login.indexOf("?") === -1 ? "?" : "&";
    location.assign(cfg.login + join + "next=" + encodeURIComponent(next));
  }

  ["keydown", "pointerdown", "input", "touchstart"].forEach(function (name) {
    document.addEventListener(name, onActivity, { passive: true, capture: true });
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") check();
  });
  restoreDraft();
  schedule();
})();
