// Calendar month view (Joel, 20 Oct 2026): weeks scroll from 3 months back to 12 ahead. Each month opens
// with a heading that CSS keeps at the top while that month is in view; this opens the view on the chosen
// month and keeps the page title on the same month as that heading. No timers, nothing sent anywhere.
(function () {
  // The month box takes the height from its own top to the bottom of the screen (28 Oct 2026): what sits above it
  // (the selected day, the period, Text notices, Print) can wrap to a second row on a laptop, so its top is
  // measured rather than assumed. CSS shares that height between the open month's weeks.
  function fit(box) {
    var holder = box.closest(".cal-workspace");
    if (!holder) return;
    var top = box.getBoundingClientRect().top + window.pageYOffset;
    holder.style.setProperty("--cal-avail", Math.max(0, Math.floor(window.innerHeight - top - 5)) + "px");
  }
  function setUp(box) {
    fit(box);
    var title = document.querySelector("[data-month-title-live]");
    var starts = box.querySelectorAll(".home-week[data-month-anchor]");
    var band = box.querySelector(".cal-month-band");
    var bandHeight = band ? band.offsetHeight : 0;
    var anchor = box.querySelector('.home-week[data-month-anchor="' + box.getAttribute("data-open-month") + '"]');
    // The box is positioned, so offsets are inside it; open with the month's heading at the top.
    if (anchor) box.scrollTop = anchor.offsetTop - bandHeight;
    // The weekday header leaves room for the scrollbar, so the day columns line up.
    var head = box.parentNode.querySelector(".home-dow");
    if (head) head.style.paddingRight = (box.offsetWidth - box.clientWidth) + "px";
    if (!title || !starts.length) return;
    var pending = false;
    function follow() {
      pending = false;
      // The month whose heading is at the top: the last month whose heading has reached the top.
      var current = starts[0];
      for (var i = 0; i < starts.length; i++) {
        if (starts[i].offsetTop - bandHeight <= box.scrollTop + 1) current = starts[i]; else break;
      }
      var text = current.getAttribute("data-month-title");
      if (text && title.textContent !== text) title.textContent = text;
    }
    box.addEventListener("scroll", function () {
      if (!pending) { pending = true; window.requestAnimationFrame(follow); }
    }, { passive: true });
    follow();
  }
  function run() {
    var boxes = document.querySelectorAll("[data-month-scroll]");
    for (var i = 0; i < boxes.length; i++) setUp(boxes[i]);
    var waiting = false;
    window.addEventListener("resize", function () {
      if (waiting) return;
      waiting = true;
      window.requestAnimationFrame(function () {
        waiting = false;
        for (var j = 0; j < boxes.length; j++) fit(boxes[j]);
      });
    }, { passive: true });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
