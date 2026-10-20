// Calendar Day and Week (Joel, 20 Oct 2026): all 24 hours scroll inside the grid. Open at the hour the
// page asks for (7 AM, or the earliest appointment in view). No timers, nothing sent anywhere.
(function () {
  function open(body) {
    var hour = parseInt(body.getAttribute("data-open-hour"), 10);
    if (isNaN(hour)) return;
    body.scrollTop = Math.round((body.scrollHeight / 24) * hour);
    // The header and all-day rows leave room for the scrollbar, so the day columns line up.
    var grid = body.closest(".cal-hours");
    if (grid) grid.style.setProperty("--cal-scrollbar", (body.offsetWidth - body.clientWidth) + "px");
  }
  function run() {
    var bodies = document.querySelectorAll(".cal-hours-body[data-open-hour]");
    for (var i = 0; i < bodies.length; i++) open(bodies[i]);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
