/* Show or hide the password on the sign-in pages (office and supplier). The field returns to hidden
   before the form is sent, so a browser never stores it as plain text (Joel, 17 Oct 2026). */
(function () {
  var EYE = '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 19c-7 0-11-7-11-7a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/></svg>';
  document.querySelectorAll("input[data-password-reveal]").forEach(function (input) {
    var wrap = document.createElement("span");
    wrap.className = "password-reveal";
    // Moving the field into its wrapper takes the focus from it. Someone already typing there (the page still loading)
    // keeps the focus and the cursor or selection (6 Nov 2026: the keys typed next went nowhere).
    var focused = document.activeElement === input;
    var start = null, end = null, direction = null;
    if (focused) {
      try {
        start = input.selectionStart; end = input.selectionEnd; direction = input.selectionDirection;
      } catch (err) {
        /* no selection on this field type */
      }
    }
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    if (focused && document.activeElement !== input) {
      input.focus();
      if (start !== null && end !== null) {
        try {
          input.setSelectionRange(start, end, direction || "none");
        } catch (err) {
          /* no selection on this field type */
        }
      }
    }
    var button = document.createElement("button");
    button.type = "button";
    button.className = "password-reveal-toggle";
    button.setAttribute("data-password-reveal-toggle", "");
    function show(visible) {
      input.type = visible ? "text" : "password";
      button.setAttribute("aria-pressed", visible ? "true" : "false");
      button.setAttribute("aria-label", visible ? "Hide password" : "Show password");
      button.title = visible ? "Hide password" : "Show password";
      button.innerHTML = visible ? EYE_OFF : EYE;
    }
    show(false);
    button.addEventListener("click", function () {
      show(input.type === "password");
      input.focus();
    });
    wrap.appendChild(button);
    if (input.form) {
      input.form.addEventListener("submit", function () { show(false); });
    }
  });
})();
