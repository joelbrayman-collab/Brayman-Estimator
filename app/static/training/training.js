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
  // Step check-offs: tick a step and it turns green at once; the tick is saved on the server.
  document.querySelectorAll("[data-tick-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch", "X-CSRFToken": token } })
        .then(function (r) { if (!r.ok) throw new Error("not saved"); return r.json(); })
        .then(function (data) {
          var card = form.closest("[data-step-card]");
          var btn = form.querySelector("[data-tick]");
          var n = Number(card.getAttribute("data-step-card")) + 1;
          card.classList.toggle("is-done", data.done);
          btn.classList.toggle("is-done", data.done);
          btn.setAttribute("aria-pressed", data.done ? "true" : "false");
          btn.querySelector(".tc-tick-box").textContent = data.done ? "\u2713" : "";
          btn.querySelector(".tc-tick-label").textContent = data.done ? "Done" : "I did this step";
          card.querySelector(".tc-check").textContent = data.done ? "\u2713" : String(n);
          form.querySelector('[name="done"]').value = data.done ? "0" : "1";
          var count = document.querySelector("[data-ticked]"); if (count) count.textContent = data.ticked;
          var bar = document.querySelector("[data-step-bar]"); if (bar) bar.style.width = Math.round(100 * data.ticked / data.total) + "%";
          document.querySelectorAll("[data-step-card]").forEach(function (c) { c.classList.remove("is-current"); });
          var next = document.querySelector("[data-step-card]:not(.is-done)");
          if (data.done) {
            if (next) { next.classList.add("is-current"); next.scrollIntoView({ behavior: "smooth", block: "start" }); }
            else { var ex = document.getElementById("exercise"); if (ex) ex.scrollIntoView({ behavior: "smooth", block: "start" }); }
          }
        })
        .catch(function () { form.submit(); });
    });
  });
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
