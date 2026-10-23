// Calendar Mon–Fri / Full week (Joel, 23 Oct 2026). Shows or hides Saturday and Sunday in the Month and
// Week views and remembers the choice on this device for this person. Nothing is sent anywhere; print
// always lists every day. Without this script the calendar shows the full week.
(function () {
  function run() {
    var sw = document.querySelector("[data-days-switch]");
    var workspace = document.querySelector(".cal-workspace");
    if (!sw || !workspace) return;
    var key = sw.getAttribute("data-days-key");
    var buttons = sw.querySelectorAll("[data-days-choice]");
    function show(days) {
      workspace.setAttribute("data-days", days);
      for (var i = 0; i < buttons.length; i++) {
        buttons[i].setAttribute("aria-pressed", buttons[i].getAttribute("data-days-choice") === days ? "true" : "false");
      }
    }
    show(workspace.getAttribute("data-days") === "5" ? "5" : "7");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function (event) {
        var days = event.currentTarget.getAttribute("data-days-choice");
        show(days);
        try { window.localStorage.setItem(key, days); } catch (e) { /* private window: this page only */ }
      });
    }
    sw.hidden = false;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
