(function () {
  var token = (document.querySelector('meta[name="csrf-token"]') || {}).content || "";
  // Screenshot full size.
  var box = document.querySelector("[data-lightbox]");
  document.querySelectorAll("[data-enlarge]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (!box || !box.showModal) { window.open(btn.querySelector("img").src, "_blank"); return; }
      var img = box.querySelector("img"); var src = btn.querySelector("img");
      img.src = src.src; img.alt = src.alt; box.showModal();
    });
  });
  if (box) box.addEventListener("click", function (e) { if (e.target === box || e.target.tagName === "IMG") box.close(); });
  // Tutor: minimize and restore without leaving the page (the choice is saved on the server).
  var tutor = document.querySelector("[data-tutor]");
  if (!tutor) return;
  var toggle = tutor.querySelector("[data-tutor-toggle]");
  toggle.addEventListener("submit", function (e) {
    e.preventDefault();
    var input = toggle.querySelector('[name="minimized"]');
    var body = new FormData(toggle);
    fetch(toggle.action, { method: "POST", body: body, headers: { "X-Requested-With": "fetch", "X-CSRFToken": token } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        tutor.classList.toggle("is-min", data.minimized);
        input.value = data.minimized ? "0" : "1";
        toggle.querySelector("[data-tutor-button]").textContent = data.minimized ? "Open the Tutor" : "Minimize";
      })
      .catch(function () { toggle.submit(); });
  });
  var ask = tutor.querySelector("[data-tutor-ask]");
  var out = tutor.querySelector("[data-tutor-answer][hidden]") || tutor.querySelector("[data-tutor-answer]");
  ask.addEventListener("submit", function (e) {
    e.preventDefault();
    var body = new FormData(ask);
    fetch(ask.action, { method: "POST", body: body, headers: { "X-Requested-With": "fetch", "X-CSRFToken": token } })
      .then(function (r) { return r.json(); })
      .then(function (data) { out.textContent = data.answer; out.hidden = false; })
      .catch(function () { ask.submit(); });
  });
})();
