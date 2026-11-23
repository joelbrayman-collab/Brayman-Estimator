/* Prepare my estimate: the AI can take a minute or two. Show that it is working, with a running timer, and stop a second click. */
(function () {
  var form = document.querySelector("[data-prepare-estimate] form");
  if (!form) return;
  form.addEventListener("submit", function () {
    var button = form.querySelector("button[type=submit]");
    var note = document.createElement("p");
    note.className = "ge-working";
    note.setAttribute("role", "status");
    note.setAttribute("data-prepare-progress", "");
    note.innerHTML = '<span class="ge-spinner" aria-hidden="true"></span> <strong>Reading your drawings…</strong> ' +
      'This can take up to 2 minutes. Please keep this page open. <span data-elapsed>0:00</span>';
    form.appendChild(note);
    if (button) { button.textContent = "WORKING…"; window.setTimeout(function () { button.disabled = true; }, 0); }
    var started = Date.now(), clock = note.querySelector("[data-elapsed]");
    window.setInterval(function () {
      var s = Math.floor((Date.now() - started) / 1000);
      clock.textContent = Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
    }, 1000);
  });
})();
