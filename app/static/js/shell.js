(function () {
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
