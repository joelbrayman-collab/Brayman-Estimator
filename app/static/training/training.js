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
  // The Tutor follows the step the trainee is on (a ticked step moves it on; tapping a step points it there).
  function followStep(card) {
    var tutor = document.querySelector("[data-tutor]");
    if (!tutor || !card) return;
    var n = Number(card.getAttribute("data-step-card"));
    var set = function (sel, val) { var el = tutor.querySelector(sel); if (el) el.textContent = val; };
    set("[data-tutor-number]", String(n + 1));
    var title = tutor.querySelector("[data-tutor-title]");
    if (title) title.innerHTML = "Step <span data-tutor-number>" + (n + 1) + "</span>: ";
    if (title) title.appendChild(document.createTextNode(card.getAttribute("data-t-title")));
    set("[data-tutor-why]", card.getAttribute("data-t-why"));
    set("[data-tutor-app]", card.getAttribute("data-t-app"));
    set("[data-tutor-where]", card.getAttribute("data-t-where"));
    set("[data-tutor-do]", card.getAttribute("data-t-do"));
    set("[data-tutor-expect]", card.getAttribute("data-t-expect"));
    var input = tutor.querySelector("[data-tutor-step-input]"); if (input) input.value = String(n);
    tutor.setAttribute("data-step", String(n));
  }
  document.querySelectorAll("[data-step-card]").forEach(function (card) {
    card.addEventListener("click", function (e) {
      if (e.target.closest("button, a, input, summary, form")) return;
      document.querySelectorAll("[data-step-card]").forEach(function (c) { c.classList.remove("is-current"); });
      card.classList.add("is-current");
      followStep(card);
    });
  });

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
            if (next) { next.classList.add("is-current"); followStep(next); next.scrollIntoView({ behavior: "smooth", block: "start" }); }
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
        var b = toggle.querySelector("[data-tutor-button]");
        b.textContent = data.minimized ? "Open the Tutor" : "Minimize";
        b.setAttribute("aria-expanded", data.minimized ? "false" : "true");
      })
      .catch(function () { toggle.submit(); });
  });
  var ask = tutor.querySelector("[data-tutor-ask]");
  tutor.querySelectorAll("[data-tutor-quick]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      ask.querySelector('[name="question"]').value = chip.getAttribute("data-tutor-quick");
      if (ask.requestSubmit) ask.requestSubmit(); else ask.dispatchEvent(new Event("submit", { cancelable: true }));
    });
  });
  var out = tutor.querySelector("[data-tutor-live]");
  ask.addEventListener("submit", function (e) {
    e.preventDefault();
    var body = new FormData(ask);
    fetch(ask.action, { method: "POST", body: body, headers: { "X-Requested-With": "fetch", "X-CSRFToken": token } })
      .then(function (r) { return r.json(); })
      .then(function (data) { out.textContent = data.answer; out.hidden = false; })
      .catch(function () { ask.submit(); });
  });
})();
