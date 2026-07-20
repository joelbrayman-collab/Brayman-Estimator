/**
 * Global Search / Command Palette
 *
 * Reusable UI foundation. Sample in-memory data only — swap the provider
 * later for SQLAlchemy-backed search without changing the shell.
 */
(function () {
  const MODULE_ORDER = [
    "Actions",
    "Clients",
    "Projects",
    "Estimates",
    "Assemblies",
    "Cost Library",
    "Change Orders",
    "Proposal Templates",
  ];

  const SAMPLE_RECORDS = [
    {
      id: "client-1",
      icon: "bi-people",
      title: "Allegheny Bridge Authority",
      subtitle: "Municipal · Pittsburgh, PA",
      module: "Clients",
      route: "/clients/",
      keywords: ["aba", "bridge", "municipal"],
    },
    {
      id: "client-2",
      icon: "bi-people",
      title: "Ohio River Logistics",
      subtitle: "Private · Cincinnati, OH",
      module: "Clients",
      route: "/clients/",
      keywords: ["orl", "logistics", "river"],
    },
    {
      id: "client-3",
      icon: "bi-people",
      title: "West Virginia DOT",
      subtitle: "Agency · Charleston, WV",
      module: "Clients",
      route: "/clients/",
      keywords: ["wvdot", "dot", "agency"],
    },
    {
      id: "project-1",
      icon: "bi-building",
      title: "I-79 Pier Rehabilitation",
      subtitle: "Active · Allegheny Bridge Authority",
      module: "Projects",
      route: "/projects/",
      keywords: ["i-79", "pier", "rehab"],
    },
    {
      id: "project-2",
      icon: "bi-building",
      title: "Monongahela Dock Expansion",
      subtitle: "Bidding · Ohio River Logistics",
      module: "Projects",
      route: "/projects/",
      keywords: ["dock", "monongahela", "expansion"],
    },
    {
      id: "project-3",
      icon: "bi-building",
      title: "Route 19 Slope Stabilization",
      subtitle: "Planning · West Virginia DOT",
      module: "Projects",
      route: "/projects/",
      keywords: ["route 19", "slope", "stabilization"],
    },
    {
      id: "estimate-1",
      icon: "bi-calculator",
      title: "EST-000142 · Pier Rehab Bid",
      subtitle: "Draft · I-79 Pier Rehabilitation",
      module: "Estimates",
      route: "/estimates/",
      keywords: ["est", "bid", "pier"],
    },
    {
      id: "estimate-2",
      icon: "bi-calculator",
      title: "EST-000158 · Dock Expansion",
      subtitle: "Issued · Monongahela Dock Expansion",
      module: "Estimates",
      route: "/estimates/",
      keywords: ["est", "dock"],
    },
    {
      id: "estimate-3",
      icon: "bi-calculator",
      title: "EST-000171 · Slope Stabilization",
      subtitle: "In Review · Route 19 Slope Stabilization",
      module: "Estimates",
      route: "/estimates/",
      keywords: ["est", "slope"],
    },
    {
      id: "assembly-1",
      icon: "bi-layers",
      title: "Cast-in-Place Pier Cap",
      subtitle: "Structural · Concrete",
      module: "Assemblies",
      route: "/assemblies/",
      keywords: ["cip", "pier", "cap", "concrete"],
    },
    {
      id: "assembly-2",
      icon: "bi-layers",
      title: "Soldier Pile Wall",
      subtitle: "Earth Retention · Steel",
      module: "Assemblies",
      route: "/assemblies/",
      keywords: ["soldier", "pile", "wall"],
    },
    {
      id: "assembly-3",
      icon: "bi-layers",
      title: "Drilled Shaft 48in",
      subtitle: "Foundations · Deep",
      module: "Assemblies",
      route: "/assemblies/",
      keywords: ["drilled", "shaft", "caisson"],
    },
    {
      id: "cost-1",
      icon: "bi-box-seam",
      title: "Ready-Mix Concrete 4000 PSI",
      subtitle: "Material · CY",
      module: "Cost Library",
      route: "/cost-library/",
      keywords: ["concrete", "ready-mix", "4000"],
    },
    {
      id: "cost-2",
      icon: "bi-box-seam",
      title: "Ironworker — Structural",
      subtitle: "Labor · HR",
      module: "Cost Library",
      route: "/cost-library/",
      keywords: ["ironworker", "labor", "structural"],
    },
    {
      id: "cost-3",
      icon: "bi-box-seam",
      title: "Crawler Crane 100-Ton",
      subtitle: "Equipment · DAY",
      module: "Cost Library",
      route: "/cost-library/",
      keywords: ["crane", "crawler", "equipment"],
    },
    {
      id: "co-1",
      icon: "bi-arrow-left-right",
      title: "CO-000012 · Additional Pier Caps",
      subtitle: "Pending Approval · I-79 Pier Rehabilitation",
      module: "Change Orders",
      route: "/project-controls/change-orders",
      keywords: ["co", "pier", "caps"],
    },
    {
      id: "co-2",
      icon: "bi-arrow-left-right",
      title: "CO-000018 · Dock Fender Upgrade",
      subtitle: "Draft · Monongahela Dock Expansion",
      module: "Change Orders",
      route: "/project-controls/change-orders",
      keywords: ["co", "fender", "dock"],
    },
    {
      id: "template-1",
      icon: "bi-file-earmark-richtext",
      title: "Standard Lump Sum Proposal",
      subtitle: "Default · Commercial",
      module: "Proposal Templates",
      route: "/proposal-templates/",
      keywords: ["lump sum", "proposal", "template"],
    },
    {
      id: "template-2",
      icon: "bi-file-earmark-richtext",
      title: "Unit Price DOT Proposal",
      subtitle: "Agency · Public Works",
      module: "Proposal Templates",
      route: "/proposal-templates/",
      keywords: ["unit price", "dot", "template"],
    },
  ];

  const SAMPLE_ACTIONS = [
    {
      id: "action-new-estimate",
      icon: "bi-plus-circle",
      title: "New estimate",
      subtitle: "Create a new estimate",
      module: "Actions",
      route: "/estimates/new",
      match: ["new estimate", "create estimate"],
      hint: "↵",
    },
    {
      id: "action-new-client",
      icon: "bi-plus-circle",
      title: "New client",
      subtitle: "Add a client record",
      module: "Actions",
      route: "/clients/new",
      match: ["new client", "create client", "add client"],
      hint: "↵",
    },
    {
      id: "action-new-project",
      icon: "bi-plus-circle",
      title: "New project",
      subtitle: "Start a new project",
      module: "Actions",
      route: "/projects/new",
      match: ["new project", "create project", "add project"],
      hint: "↵",
    },
    {
      id: "action-new-proposal",
      icon: "bi-plus-circle",
      title: "New proposal",
      subtitle: "Generate a proposal (placeholder)",
      module: "Actions",
      route: "/proposals",
      match: ["new proposal", "create proposal"],
      hint: "↵",
    },
  ];

  /** Default search provider — replace with async API later. */
  function sampleSearchProvider(query) {
    const q = String(query || "")
      .trim()
      .toLowerCase();
    const actions = SAMPLE_ACTIONS.filter(function (action) {
      if (!q) {
        return false;
      }
      if (action.title.toLowerCase().includes(q)) {
        return true;
      }
      return action.match.some(function (phrase) {
        return phrase.includes(q) || q.includes(phrase);
      });
    });

    const records = SAMPLE_RECORDS.filter(function (item) {
      if (!q) {
        return true;
      }
      const haystack = [
        item.title,
        item.subtitle,
        item.module,
        (item.keywords || []).join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });

    return { actions: actions, records: records };
  }

  let searchProvider = sampleSearchProvider;

  const root = document.getElementById("command-palette");
  const dialog = root ? root.querySelector(".command-palette-dialog") : null;
  const input = document.getElementById("command-palette-input");
  const resultsEl = document.getElementById("command-palette-results");
  const trigger = document.getElementById("header-search-trigger");
  const shortcutBadges = document.querySelectorAll("[data-search-shortcut]");

  if (!root || !dialog || !input || !resultsEl) {
    return;
  }

  let open = false;
  let activeIndex = 0;
  let flatItems = [];
  let lastQuery = "";

  function isApplePlatform() {
    const platform = navigator.platform || "";
    const ua = navigator.userAgent || "";
    return /Mac|iPhone|iPad|iPod/i.test(platform) || /Mac OS X/i.test(ua);
  }

  function shortcutLabel() {
    return isApplePlatform() ? "⌘K" : "Ctrl+K";
  }

  function applyShortcutBadges() {
    const label = shortcutLabel();
    shortcutBadges.forEach(function (el) {
      el.textContent = label;
    });
  }

  function setOpen(next) {
    open = Boolean(next);
    root.hidden = !open;
    root.setAttribute("aria-hidden", open ? "false" : "true");
    document.body.classList.toggle("command-palette-open", open);
    if (trigger) {
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    }
    if (open) {
      input.value = "";
      lastQuery = "";
      renderResults("");
      window.requestAnimationFrame(function () {
        input.focus();
        input.select();
      });
    } else {
      flatItems = [];
      activeIndex = 0;
    }
  }

  function groupByModule(records) {
    const groups = {};
    records.forEach(function (item) {
      if (!groups[item.module]) {
        groups[item.module] = [];
      }
      groups[item.module].push(item);
    });
    return MODULE_ORDER.filter(function (name) {
      return groups[name] && groups[name].length;
    }).map(function (name) {
      return { module: name, items: groups[name] };
    });
  }

  function renderItem(item, index) {
    const isActive = index === activeIndex;
    const hint = item.hint
      ? '<span class="command-palette-hint">' + escapeHtml(item.hint) + "</span>"
      : "";
    return (
      '<button type="button" class="command-palette-item' +
      (isActive ? " is-active" : "") +
      '" role="option" id="command-palette-option-' +
      index +
      '" data-index="' +
      index +
      '" aria-selected="' +
      (isActive ? "true" : "false") +
      '">' +
      '<span class="command-palette-item-icon" aria-hidden="true">' +
      '<i class="bi ' +
      escapeHtml(item.icon) +
      '"></i>' +
      "</span>" +
      '<span class="command-palette-item-copy">' +
      '<span class="command-palette-item-title">' +
      escapeHtml(item.title) +
      "</span>" +
      '<span class="command-palette-item-subtitle">' +
      escapeHtml(item.subtitle) +
      "</span>" +
      "</span>" +
      hint +
      "</button>"
    );
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderResults(query) {
    const result = searchProvider(query) || { actions: [], records: [] };
    const actions = result.actions || [];
    const records = result.records || [];
    flatItems = actions.concat(records);
    if (activeIndex >= flatItems.length) {
      activeIndex = Math.max(0, flatItems.length - 1);
    }

    if (!flatItems.length) {
      resultsEl.innerHTML =
        '<div class="command-palette-empty">' +
        "<p>No matches</p>" +
        "<p class=\"command-palette-empty-hint\">Try a client, project, estimate, or type “new estimate”.</p>" +
        "</div>";
      input.removeAttribute("aria-activedescendant");
      return;
    }

    let html = "";
    let index = 0;

    if (actions.length) {
      html += '<section class="command-palette-group">';
      html += '<p class="command-palette-group-label">Actions</p>';
      html += '<div class="command-palette-group-list" role="presentation">';
      actions.forEach(function (item) {
        html += renderItem(item, index);
        index += 1;
      });
      html += "</div></section>";
    }

    groupByModule(records).forEach(function (group) {
      html += '<section class="command-palette-group">';
      html +=
        '<p class="command-palette-group-label">' +
        escapeHtml(group.module) +
        "</p>";
      html += '<div class="command-palette-group-list" role="presentation">';
      group.items.forEach(function (item) {
        html += renderItem(item, index);
        index += 1;
      });
      html += "</div></section>";
    });

    resultsEl.innerHTML = html;
    syncActiveOption();
  }

  function syncActiveOption() {
    const options = resultsEl.querySelectorAll(".command-palette-item");
    options.forEach(function (el, idx) {
      const isActive = idx === activeIndex;
      el.classList.toggle("is-active", isActive);
      el.setAttribute("aria-selected", isActive ? "true" : "false");
      if (isActive) {
        input.setAttribute("aria-activedescendant", el.id);
        el.scrollIntoView({ block: "nearest" });
      }
    });
  }

  function moveActive(delta) {
    if (!flatItems.length) {
      return;
    }
    const next = (activeIndex + delta + flatItems.length) % flatItems.length;
    activeIndex = next;
    syncActiveOption();
  }

  function activateItem(item) {
    if (!item || !item.route) {
      return;
    }
    setOpen(false);
    window.location.href = item.route;
  }

  function activateActive() {
    if (!flatItems.length) {
      return;
    }
    activateItem(flatItems[activeIndex]);
  }

  function onTriggerClick(event) {
    event.preventDefault();
    setOpen(true);
  }

  if (trigger) {
    trigger.addEventListener("click", onTriggerClick);
  }

  root.addEventListener("click", function (event) {
    if (event.target === root) {
      setOpen(false);
    }
  });

  resultsEl.addEventListener("click", function (event) {
    const button = event.target.closest(".command-palette-item");
    if (!button) {
      return;
    }
    const index = Number(button.getAttribute("data-index"));
    if (!Number.isNaN(index) && flatItems[index]) {
      activateItem(flatItems[index]);
    }
  });

  resultsEl.addEventListener("mousemove", function (event) {
    const button = event.target.closest(".command-palette-item");
    if (!button) {
      return;
    }
    const index = Number(button.getAttribute("data-index"));
    if (!Number.isNaN(index) && index !== activeIndex) {
      activeIndex = index;
      syncActiveOption();
    }
  });

  input.addEventListener("input", function () {
    const query = input.value;
    if (query === lastQuery) {
      return;
    }
    lastQuery = query;
    activeIndex = 0;
    renderResults(query);
  });

  input.addEventListener("keydown", function (event) {
    if (!open) {
      return;
    }
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        moveActive(1);
        break;
      case "ArrowUp":
        event.preventDefault();
        moveActive(-1);
        break;
      case "Enter":
        event.preventDefault();
        activateActive();
        break;
      case "Escape":
        event.preventDefault();
        event.stopPropagation();
        setOpen(false);
        break;
      case "Tab":
        event.preventDefault();
        moveActive(event.shiftKey ? -1 : 1);
        break;
      default:
        break;
    }
  });

  document.addEventListener(
    "keydown",
    function (event) {
      const key = event.key;
      const isK = key === "k" || key === "K";
      if (isK && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen(!open);
        return;
      }
      if (open && key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        setOpen(false);
      }
    },
    true
  );

  applyShortcutBadges();

  window.BraymanCommandPalette = {
    open: function () {
      setOpen(true);
    },
    close: function () {
      setOpen(false);
    },
    isOpen: function () {
      return open;
    },
    setProvider: function (provider) {
      if (typeof provider === "function") {
        searchProvider = provider;
      }
    },
    resetProvider: function () {
      searchProvider = sampleSearchProvider;
    },
  };
})();
