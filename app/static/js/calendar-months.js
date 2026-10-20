// Calendar month view (Joel, 20 Oct 2026): weeks scroll from 3 months back to 12 ahead. Open on the
// chosen month and keep the title on the month at the top. No timers, nothing sent anywhere.
(function () {
  function setUp(box) {
    var title = document.querySelector("[data-month-title-live]");
    var weeks = box.querySelectorAll(".home-week[data-month-title]");
    var anchor = box.querySelector('[data-month-anchor="' + box.getAttribute("data-open-month") + '"]');
    if (anchor) box.scrollTop = anchor.offsetTop;  // the box is positioned, so offsets are inside it
    // The weekday header leaves room for the scrollbar, so the day columns line up.
    var head = box.parentNode.querySelector(".home-dow");
    if (head) head.style.paddingRight = (box.offsetWidth - box.clientWidth) + "px";
    if (!title || !weeks.length) return;
    var pending = false;
    function follow() {
      pending = false;
      var top = box.scrollTop + 24;
      var current = weeks[0];
      for (var i = 0; i < weeks.length; i++) {
        if (weeks[i].offsetTop <= top) current = weeks[i]; else break;
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
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
