// Workflow Map (Joel, 21 Oct 2026): instant moves between stages, Back / Next, arrow keys.
// Every control is a real link (?stage=…), so the map also works without this file.
(function () {
  "use strict";
  var root = document.querySelector("[data-wf-map]");
  if (!root) return;
  var total = root.querySelectorAll("[data-wf-page]").length;
  var tabs = root.querySelector("[data-wf-journey-tabs]");

  function page(id) { return root.querySelector('[data-wf-page="' + id + '"]'); }
  function current() { return root.getAttribute("data-wf-current"); }

  function setLink(el, id) {
    if (!el) return;
    if (id && page(id)) {
      el.setAttribute("href", page(id).getAttribute("data-wf-href"));
      el.setAttribute("data-wf-goto", id);
      el.removeAttribute("aria-disabled");
    } else {
      el.setAttribute("href", "#workflow-stage");
      el.removeAttribute("data-wf-goto");
      el.setAttribute("aria-disabled", "true");
    }
  }

  function show(id, opts) {
    var target = page(id);
    if (!target) return false;
    opts = opts || {};
    root.querySelectorAll("[data-wf-page]").forEach(function (p) { p.hidden = p !== target; });
    root.querySelectorAll("[data-wf-card]").forEach(function (c) {
      var on = c.getAttribute("data-wf-card") === id;
      c.classList.toggle("is-current", on);
      c.setAttribute("aria-expanded", on ? "true" : "false");
      if (on) c.setAttribute("aria-current", "step"); else c.removeAttribute("aria-current");
    });
    root.querySelectorAll("[data-wf-step]").forEach(function (li) {
      var on = li.getAttribute("data-wf-step") === id;
      li.classList.toggle("is-current", on);
      var a = li.querySelector("a");
      if (on) a.setAttribute("aria-current", "step"); else a.removeAttribute("aria-current");
    });
    root.querySelectorAll("[data-wf-journey]").forEach(function (nav) {
      nav.classList.toggle("is-current-journey", !!nav.querySelector('[data-wf-step="' + id + '"]'));
    });
    // Several journeys (24 Oct 2026): only the current stage's journey is shown; the selector follows it.
    if (tabs) {
      var jkey = target.getAttribute("data-wf-jkey");
      root.querySelectorAll("[data-wf-journey]").forEach(function (nav) { nav.hidden = nav.getAttribute("data-wf-journey") !== jkey; });
      root.querySelectorAll("[data-wf-journey-map]").forEach(function (m) { m.hidden = m.getAttribute("data-wf-journey-map") !== jkey; });
      tabs.querySelectorAll("[data-wf-journey-tab]").forEach(function (t) {
        var on = t.getAttribute("data-wf-journey-tab") === jkey;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
      });
    }
    root.setAttribute("data-wf-current", id);
    setLink(root.querySelector("[data-wf-control-back]"), target.getAttribute("data-wf-prev"));
    setLink(root.querySelector("[data-wf-control-next]"), target.getAttribute("data-wf-next"));
    var count = root.querySelector("[data-wf-count]");
    if (count) count.textContent = target.getAttribute("data-wf-position") + " of " + total + " · " + target.getAttribute("data-wf-label");
    var stageInput = root.querySelector("[data-wf-stage-input]");
    if (stageInput) stageInput.value = id;
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("stage", id);
      url.hash = "";
      window.history.replaceState(null, "", url.toString());
    } catch (e) { /* the page still works */ }
    if (opts.focus !== false) {
      var h = target.querySelector("h2");
      if (h) h.focus({ preventScroll: true });
      var narrow = window.matchMedia("(max-width: 959px)").matches;
      if (narrow || opts.scroll) target.scrollIntoView({ block: "start", behavior: "smooth" });
    }
    return true;
  }

  // The journey selector: one click (or Enter) opens the journey at its first stage; the arrow keys, Home and
  // End move between journeys (a tablist), without moving the stage page under the trainee's focus.
  function selectJourney(tab, focusTab) {
    if (!show(tab.getAttribute("data-wf-first"), { focus: false })) return false;
    if (focusTab) tab.focus();
    return true;
  }
  if (tabs) {
    tabs.addEventListener("keydown", function (ev) {
      var list = Array.prototype.slice.call(tabs.querySelectorAll("[data-wf-journey-tab]"));
      var i = list.indexOf(ev.target.closest("[data-wf-journey-tab]"));
      if (i < 0) return;
      var n = ev.key === "ArrowRight" || ev.key === "ArrowDown" ? (i + 1) % list.length
        : ev.key === "ArrowLeft" || ev.key === "ArrowUp" ? (i - 1 + list.length) % list.length
        : ev.key === "Home" ? 0 : ev.key === "End" ? list.length - 1 : -1;
      if (n < 0) return;
      ev.preventDefault();
      ev.stopPropagation();
      selectJourney(list[n], true);
    });
  }

  root.addEventListener("click", function (ev) {
    var tab = ev.target.closest("[data-wf-journey-tab]");
    if (tab && root.contains(tab)) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button === 1) return;
      if (selectJourney(tab, false)) ev.preventDefault();
      return;
    }
    var a = ev.target.closest("[data-wf-goto]");
    if (a && root.contains(a)) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button === 1) return;
      if (show(a.getAttribute("data-wf-goto"))) ev.preventDefault();
      return;
    }
    var disabled = ev.target.closest('[aria-disabled="true"]');
    if (disabled && root.contains(disabled)) { ev.preventDefault(); return; }
    if (ev.target.closest("[data-wf-show-map]")) {
      ev.preventDefault();
      var card = root.querySelector('[data-wf-card="' + current() + '"]') || root.querySelector("[data-wf-card]");
      var map = document.getElementById("wf-overview");
      if (map) map.scrollIntoView({ block: "start", behavior: "smooth" });
      if (card) card.focus({ preventScroll: true });
      return;
    }
    if (ev.target.closest("[data-wf-open-cal]")) {
      var cal = document.getElementById("cal-launch");
      if (cal) { ev.preventDefault(); cal.click(); }
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    var t = ev.target;
    if (t && (t.isContentEditable || /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName))) return;
    if (document.querySelector("dialog[open]")) return;
    var p = page(current());
    var id = p && p.getAttribute(ev.key === "ArrowLeft" ? "data-wf-prev" : "data-wf-next");
    if (id && show(id)) ev.preventDefault();
  });
})();
