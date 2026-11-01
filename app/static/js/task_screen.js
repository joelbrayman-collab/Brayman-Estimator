// Task Screen behaviour (Task-First UX, 31 Oct 2026).
// An attention item or a link may point at an exact place on a page (#hub-punch-list, #share-12). When that
// place sits inside a closed Details section, open every enclosing <details> so the person lands on the
// decision itself, not on a closed box.
(function () {
  "use strict";
  function reveal(hash) {
    if (!hash || hash.length < 2) return;
    var id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (e) { return; }
    var target = document.getElementById(id);
    if (!target) return;
    var opened = false;
    for (var node = target; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) { node.open = true; opened = true; }
    }
    if (opened) target.scrollIntoView({ block: "start" });
  }
  function onHash() { reveal(window.location.hash); }
  document.addEventListener("DOMContentLoaded", onHash);
  window.addEventListener("hashchange", onHash);
  // In-page links (the project's section strip) open their section too.
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest('a[href^="#"]');
    if (link) reveal(link.getAttribute("href"));
  });
})();

// The header bell and the sidebar Attention item show the live count of items waiting on you.
(function () {
  "use strict";
  function fill() {
    var bell = document.querySelector("[data-attention-bell]");
    if (!bell || !window.fetch) return;
    var url = bell.getAttribute("data-attention-count-url");
    if (!url) return;
    fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || typeof data.count !== "number") return;
        var label = data.count === 1 ? "1 item needs your attention" : data.count + " items need your attention";
        bell.setAttribute("aria-label", data.count ? label : "What needs your attention");
        bell.setAttribute("title", data.count ? label : "What needs your attention");
        document.querySelectorAll("[data-attention-bell-count]").forEach(function (badge) {
          badge.textContent = data.count > 99 ? "99+" : String(data.count);
          badge.hidden = !data.count;
        });
      })
      .catch(function () {});
  }
  document.addEventListener("DOMContentLoaded", fill);
})();
