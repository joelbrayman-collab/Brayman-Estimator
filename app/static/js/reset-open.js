// Set-password link (22 Oct 2026): move the one-use credential from after "#" into the form body,
// take it out of the address bar and history, and continue. It never reaches a server log.
(function () {
  var form = document.querySelector("[data-reset-open]");
  if (!form) return;
  var credential = (window.location.hash || "").replace(/^#/, "");
  if (window.history && window.history.replaceState) {
    window.history.replaceState(null, "", window.location.pathname);
  }
  if (!/^[A-Za-z0-9_-]{8,80}\.[A-Za-z0-9_-]{16,128}$/.test(credential)) {
    form.querySelector("[data-reset-opening]").hidden = true;
    form.querySelector("[data-reset-missing]").hidden = false;
    return;
  }
  form.querySelector("[data-reset-credential]").value = credential;
  form.querySelector("[data-reset-continue]").hidden = false;
  form.submit();
})();
