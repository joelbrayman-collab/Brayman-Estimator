/* Customer fields (27 Oct 2026): the province/state list follows the country; notes grow as you type. */
(function () {
  function wire(root) {
    var country = root.querySelector("[data-country-select]");
    var region = root.querySelector("[data-region-select]");
    if (country && region) {
      var sync = function () {
        var groups = region.querySelectorAll("optgroup");
        for (var i = 0; i < groups.length; i++) {
          var show = groups[i].getAttribute("data-country") === country.value;
          groups[i].hidden = !show;
          groups[i].disabled = !show;
        }
        var chosen = region.options[region.selectedIndex];
        if (chosen && chosen.parentNode.tagName === "OPTGROUP" && chosen.parentNode.disabled) region.value = "";
      };
      country.addEventListener("change", sync);
      sync();
    }
    var notes = root.querySelectorAll("textarea[data-grow]");
    for (var j = 0; j < notes.length; j++) {
      var grow = function (el) { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight + 2, 320) + "px"; };
      notes[j].addEventListener("input", function (e) { grow(e.target); });
    }
  }
  var all = document.querySelectorAll("[data-customer-fields]");
  for (var k = 0; k < all.length; k++) wire(all[k]);
})();
