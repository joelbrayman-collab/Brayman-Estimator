/* CaliSIGN (28 Oct 2026): one deliberate press per signing action, and the typed-signature preview.
   A form marked data-calisign-once sends once: the pressed button is held and says what is happening. A field
   marked data-calisign-name mirrors into its data-calisign-preview element (the signature as it will appear).
   The server is still the guard: a second signature is refused there too. */
(function () {
  document.querySelectorAll("form[data-calisign-once]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.sent) { event.preventDefault(); return; }
      if (form.checkValidity && !form.checkValidity()) return;
      form.dataset.sent = "1";
      var button = event.submitter || form.querySelector("button[type=submit]");
      setTimeout(function () {
        form.querySelectorAll("button[type=submit]").forEach(function (b) { b.disabled = true; b.setAttribute("aria-disabled", "true"); });
        if (button) { button.dataset.label = button.textContent; button.textContent = "Working…"; }
      }, 0);
    });
  });
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) return;
    document.querySelectorAll("form[data-calisign-once]").forEach(function (form) {
      delete form.dataset.sent;
      form.querySelectorAll("button[type=submit]").forEach(function (b) { b.disabled = false; if (b.dataset.label) b.textContent = b.dataset.label; });
    });
  });
  document.querySelectorAll("[data-calisign-name]").forEach(function (input) {
    var scope = input.closest("[data-calisign-adopt]") || document;
    var preview = scope.querySelector("[data-calisign-preview]");
    if (!preview) return;
    var empty = preview.getAttribute("data-empty") || "";
    function show() { var v = (input.value || "").trim(); preview.textContent = v || empty; preview.classList.toggle("is-empty", !v); }
    input.addEventListener("input", show);
    show();
  });
})();
