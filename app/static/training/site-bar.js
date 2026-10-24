// Training site: a lesson button lands the trainee on the page with the cursor already in the field to fill in
// (23 Oct 2026). Reads the field from the bar's data-tc-focus: a field name or id, or "first" for the first field.
(function () {
  var bar = document.querySelector("[data-tc-focus]");
  if (!bar) return;
  var go = function () {
  var want = bar.getAttribute("data-tc-focus");
  var scope = document.querySelector("main") || document.body;
  var usable = function (el) {
    return el && !el.disabled && el.type !== "hidden" && el.type !== "search" && el.offsetParent !== null &&
      !el.closest("[data-training-site], nav, header, [data-help], [role=search]");
  };
  var target = null;
  if (want && want !== "first") {
    var byId = document.getElementById(want);
    var byName = scope.querySelector('[name="' + want + '"]');
    target = usable(byId) ? byId : (usable(byName) ? byName : null);
  }
  if (!target) {
    var all = scope.querySelectorAll("input, select, textarea");
    for (var i = 0; i < all.length; i++) { if (usable(all[i])) { target = all[i]; break; } }
  }
  if (!target) return;
  target.scrollIntoView({ block: "center" });
  try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }
  target.style.outline = "3px solid #c79a2b"; target.style.outlineOffset = "2px";
  };
  go();
  // Some pages move focus or scroll to a #section after they load; look once more when they are settled.
  window.addEventListener("load", function () {
    setTimeout(function () {
      var a = document.activeElement;
      if (!a || a === document.body || a === document.documentElement) go();
    }, 250);
  });
})();
