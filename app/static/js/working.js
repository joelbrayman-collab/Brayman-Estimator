/* One "working" indicator for every screen where a click makes the person wait (Joel, 23 Nov 2026).
   Mark a form: <form data-working="Reading your drawings…" data-working-note="This can take up to 2 minutes.">
   A saw cuts a board (or a hammer drives a nail: data-working-tool="hammer"), a timer runs, the button locks. */
(function () {
  var SAW = '<svg class="wk-art" viewBox="0 0 120 44" width="96" height="36" aria-hidden="true" focusable="false">' +
    '<rect x="6" y="28" width="108" height="10" rx="2" fill="#c99a2a"/><rect x="6" y="28" width="108" height="3" fill="#a77d1c"/>' +
    '<g class="wk-saw"><rect x="38" y="6" width="34" height="6" rx="3" fill="#1c1f26"/>' +
    '<path d="M42 12 H92 L88 24 H46 Z" fill="#9aa3b2"/><path d="M46 24 l3 4 l3-4 l3 4 l3-4 l3 4 l3-4 l3 4 l3-4 l3 4 l3-4 l3 4 l3-4" fill="none" stroke="#6b7384" stroke-width="2"/></g></svg>';
  var HAMMER = '<svg class="wk-art" viewBox="0 0 120 44" width="96" height="36" aria-hidden="true" focusable="false">' +
    '<rect x="6" y="36" width="108" height="6" rx="2" fill="#c99a2a"/><rect x="74" y="20" width="4" height="16" fill="#9aa3b2"/>' +
    '<rect x="70" y="17" width="12" height="4" rx="1" fill="#6b7384"/>' +
    '<g class="wk-hammer"><rect x="22" y="18" width="44" height="5" rx="2" fill="#a77d1c"/><rect x="58" y="8" width="12" height="20" rx="2" fill="#1c1f26"/></g></svg>';
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.hasAttribute || !form.hasAttribute("data-working") || form.getAttribute("data-working-started")) return;
    form.setAttribute("data-working-started", "1");
    var tool = form.getAttribute("data-working-tool") === "hammer" ? HAMMER : SAW;
    var note = document.createElement("div");
    note.className = "wk";
    note.setAttribute("role", "status");
    note.setAttribute("data-working-indicator", "");
    note.innerHTML = tool + '<div><strong></strong> <span class="wk-note"></span> <span class="wk-time" data-elapsed>0:00</span></div>';
    note.querySelector("strong").textContent = form.getAttribute("data-working") || "Working…";
    note.querySelector(".wk-note").textContent = form.getAttribute("data-working-note") || "Please keep this page open.";
    form.appendChild(note);
    Array.prototype.forEach.call(form.querySelectorAll("button[type=submit]"), function (b) {
      window.setTimeout(function () { b.disabled = true; }, 0);
    });
    var started = Date.now(), clock = note.querySelector("[data-elapsed]");
    window.setInterval(function () {
      var s = Math.floor((Date.now() - started) / 1000);
      clock.textContent = Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
    }, 1000);
  });
})();
