(function () {
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") || "" : "";
  if (csrfToken) {
    document.querySelectorAll("form").forEach(function (form) {
      const method = (form.getAttribute("method") || "get").toLowerCase();
      if (method !== "post") {
        return;
      }
      if (form.querySelector('input[name="csrf_token"]')) {
        return;
      }
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "csrf_token";
      input.value = csrfToken;
      form.appendChild(input);
    });
  }

  const body = document.body;
  const sidebar = document.getElementById("shell-sidebar");
  const overlay = document.getElementById("shell-overlay");
  const collapseBtn = document.getElementById("sidebar-collapse-btn");
  const mobileToggle = document.getElementById("mobile-nav-toggle");
  const storageKey = "brayman-shell-sidebar-collapsed";

  if (!body || !sidebar) {
    return;
  }

  function isMobile() {
    return window.matchMedia("(max-width: 900px)").matches;
  }

  function setCollapsed(collapsed) {
    body.dataset.sidebarCollapsed = collapsed ? "true" : "false";
    if (collapseBtn) {
      collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
      collapseBtn.setAttribute(
        "aria-label",
        collapsed ? "Expand sidebar" : "Collapse sidebar"
      );
      collapseBtn.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
    }
    try {
      localStorage.setItem(storageKey, collapsed ? "1" : "0");
    } catch (err) {
      /* ignore */
    }
  }

  function setMobileOpen(open) {
    body.classList.toggle("sidebar-open", open);
    if (overlay) {
      overlay.hidden = !open;
    }
    if (mobileToggle) {
      mobileToggle.setAttribute("aria-expanded", open ? "true" : "false");
      mobileToggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
      );
    }
  }

  function initCollapsedState() {
    if (isMobile()) {
      setCollapsed(false);
      setMobileOpen(false);
      return;
    }
    let collapsed = false;
    try {
      collapsed = localStorage.getItem(storageKey) === "1";
    } catch (err) {
      collapsed = window.matchMedia("(max-width: 1200px)").matches;
    }
    if (window.matchMedia("(max-width: 1200px) and (min-width: 901px)").matches) {
      collapsed = true;
    }
    setCollapsed(collapsed);
  }

  if (collapseBtn) {
    collapseBtn.addEventListener("click", function () {
      if (isMobile()) {
        setMobileOpen(false);
        return;
      }
      const next = body.dataset.sidebarCollapsed !== "true";
      setCollapsed(next);
    });
  }

  if (mobileToggle) {
    mobileToggle.addEventListener("click", function () {
      const open = !body.classList.contains("sidebar-open");
      setMobileOpen(open);
    });
  }

  if (overlay) {
    overlay.addEventListener("click", function () {
      setMobileOpen(false);
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      setMobileOpen(false);
    }
  });

  window.addEventListener("resize", function () {
    if (!isMobile()) {
      setMobileOpen(false);
    }
    initCollapsedState();
  });

  initCollapsedState();
})();

/* Collapsible sidebar groups (Calculators). Closed by default unless the current page is
   in the group; the person's choice is remembered in this browser. Every link stays reachable. */
(function () {
  document.querySelectorAll("details[data-sidebar-group]").forEach(function (group) {
    var key = "calibraytai-sidebar-group-" + group.getAttribute("data-sidebar-group");
    if (group.getAttribute("data-has-active") !== "true") {
      try {
        group.open = localStorage.getItem(key) === "open";
      } catch (err) {
        group.open = false;
      }
    }
    group.addEventListener("toggle", function () {
      try {
        localStorage.setItem(key, group.open ? "open" : "closed");
      } catch (err) {
        /* ignore */
      }
    });
  });
})();

/* Signing out of the office also empties the Field page cache on this device, so no project
   pages stay stored after the person leaves (the same clean-up Field sign-out already does). */
(function () {
  document.querySelectorAll('form[action="/logout"]').forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var controller = navigator.serviceWorker && navigator.serviceWorker.controller;
      if (!controller || form.dataset.cacheCleared === "true") {
        return;
      }
      event.preventDefault();
      var done = function () {
        form.dataset.cacheCleared = "true";
        form.submit();
      };
      var timer = window.setTimeout(done, 1500);
      navigator.serviceWorker.addEventListener("message", function onMessage(msg) {
        if (!msg.data || msg.data.type !== "field-cache-cleared") return;
        window.clearTimeout(timer);
        navigator.serviceWorker.removeEventListener("message", onMessage);
        done();
      });
      controller.postMessage({ type: "clear-field-cache" });
    });
  });
})();
