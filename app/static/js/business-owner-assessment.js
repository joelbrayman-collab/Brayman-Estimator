(function () {
  const STEPS = ["today", "business", "market", "costs", "results"];
  const form = document.getElementById("boa-form");
  const resultsRoot = document.getElementById("boa-results");
  const errorRoot = document.getElementById("boa-error");
  const csrf = document.querySelector('meta[name="csrf-token"]');
  const profiles = JSON.parse(document.getElementById("boa-profiles").textContent || "{}");
  let stepIndex = 0;

  function showStep(index) {
    stepIndex = Math.max(0, Math.min(STEPS.length - 1, index));
    const current = STEPS[stepIndex];
    document.querySelectorAll("[data-step]").forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-step") !== current;
    });
    document.querySelectorAll("[data-step-target]").forEach(function (button) {
      const name = button.getAttribute("data-step-target");
      const at = STEPS.indexOf(name);
      button.classList.toggle("is-active", name === current);
      button.classList.toggle("is-complete", at < stepIndex);
    });
    if (current === "results") {
      calculate();
    }
  }

  function collectInputs() {
    const data = {};
    new FormData(form).forEach(function (value, key) {
      data[key] = value;
    });
    return data;
  }

  function money(value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "—";
    }
    return (
      "$" +
      number.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  function hours(value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "—";
    }
    return number.toLocaleString(undefined, { maximumFractionDigits: 2 }) + " hours";
  }

  function percent(value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "—";
    }
    return number.toLocaleString(undefined, { maximumFractionDigits: 2 }) + "%";
  }

  function row(label, value) {
    return (
      '<div class="boa-row"><span>' +
      label +
      "</span><strong>" +
      value +
      "</strong></div>"
    );
  }

  function stressCard(item) {
    if (!item) {
      return "";
    }
    return (
      '<article class="boa-card"><h4>' +
      item.label +
      "</h4>" +
      row("Entrepreneurship economic value", money(item.entrepreneurship_economic_value)) +
      row("Difference vs employment", money(item.difference)) +
      row("Cash available to owner", money(item.cash_available_to_owner)) +
      "</article>"
    );
  }

  function render(result) {
    const employment = result.employment || {};
    const business = result.business || {};
    const comparison = result.comparison || {};
    const workload = result.workload || {};
    const startup = result.startup || {};
    const truth = result.what_has_to_be_true || {};
    const stress = result.stress || {};
    resultsRoot.innerHTML =
      '<div class="boa-hero">' +
      '<div class="boa-metric"><p>Employment economic value</p><strong>' +
      money(comparison.employment_economic_value) +
      "</strong></div>" +
      '<div class="boa-metric"><p>Entrepreneurship economic value</p><strong>' +
      money(comparison.entrepreneurship_economic_value) +
      "</strong></div>" +
      '<div class="boa-metric"><p>Difference</p><strong>' +
      money(comparison.difference) +
      "</strong></div>" +
      "</div>" +
      '<section class="boa-section"><h3>Cash and hours</h3><div class="boa-rows">' +
      row("Cash required to make the transition", money(startup.cash_required_to_make_transition)) +
      row(
        "Cash available to owner before personal income tax",
        money(business.cash_available_to_owner)
      ) +
      row("Owner productive / billable hours per week", hours(workload.owner_productive_hours_per_week)) +
      row("Owner admin / non-billable hours per week", hours(workload.owner_admin_hours_per_week)) +
      row("Total owner hours per week", hours(workload.owner_total_hours_per_week)) +
      row("Effective owner hourly return", money(business.effective_owner_hourly_return)) +
      row("Employment effective hourly value", money(employment.effective_hourly_value)) +
      "</div></section>" +
      '<section class="boa-section"><h3>What has to be true?</h3><p class="boa-help">Conditions under which entrepreneurship reaches the employment economic baseline. These are requirements, not a judgement.</p><div class="boa-rows">' +
      row("Required realized selling rate", money(truth.required_realized_selling_rate)) +
      row("Break-even selling rate at current productive hours", money(truth.break_even_selling_rate)) +
      row("Required productive / billable hours per week", hours(truth.required_productive_hours_per_week)) +
      row("Required owner productive hours per week", hours(truth.required_owner_productive_hours_per_week)) +
      row("Required utilization / productivity", percent(truth.required_utilization_percent)) +
      row(
        "Required total owner hours per week (productive + admin)",
        hours(truth.required_total_owner_hours_per_week)
      ) +
      "</div></section>" +
      '<section class="boa-section"><h3>If things do not go exactly as planned</h3><p class="boa-help">Three independent 10% cases from the same base inputs. The base case is not changed.</p><div class="boa-stress">' +
      stressCard(stress.base) +
      stressCard(stress.fewer_productive_hours) +
      stressCard(stress.lower_realized_rate) +
      stressCard(stress.higher_operating_costs) +
      "</div></section>" +
      (business.helper_used
        ? '<section class="boa-section"><h3>Helper / employee economics</h3><div class="boa-rows">' +
          row("Helper contribution hours per week", hours(business.helper_contribution_hours_per_week)) +
          row("Helper labour (annual)", money(business.helper_labour_annual)) +
          row("Payroll burden (annual)", money(business.helper_payroll_burden_annual)) +
          row("Helper cash cost (annual)", money(business.helper_cash_cost_annual)) +
          "</div></section>"
        : "");
  }

  function calculate() {
    errorRoot.hidden = true;
    fetch("/decision-tools/employment-vs-entrepreneurship/calculate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf ? csrf.getAttribute("content") : "",
      },
      body: JSON.stringify(collectInputs()),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Calculation was not available.");
        }
        return response.json();
      })
      .then(function (result) {
        render(result);
      })
      .catch(function () {
        errorRoot.textContent = "The comparison could not be calculated from the current inputs.";
        errorRoot.hidden = false;
      });
  }

  function downloadPdf() {
    errorRoot.hidden = true;
    const inputs = collectInputs();
    fetch("/decision-tools/employment-vs-entrepreneurship/results.pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf ? csrf.getAttribute("content") : "",
      },
      body: JSON.stringify(inputs),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("PDF was not available.");
        }
        const disposition = response.headers.get("Content-Disposition") || "";
        return response.blob().then(function (blob) {
          return { blob: blob, disposition: disposition };
        });
      })
      .then(function (payload) {
        const url = window.URL.createObjectURL(payload.blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filenameFromDisposition(payload.disposition);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(function () {
        errorRoot.textContent = "The results PDF could not be created from the current inputs.";
        errorRoot.hidden = false;
      });
  }

  function filenameFromDisposition(header) {
    const match = /filename="([^"]+)"/i.exec(header || "");
    if (match && match[1]) {
      return match[1];
    }
    return "CalibraytAI_Employment_vs_Entrepreneurship.pdf";
  }

  function startOver() {
    form.reset();
    syncPayMode();
    resultsRoot.innerHTML = "";
    errorRoot.hidden = true;
    showStep(0);
  }

  function applyProfile() {
    const select = document.getElementById("trade_profile");
    const profile = profiles[select.value] || {};
    if (profile.realized_hourly_rate) {
      document.getElementById("realized_hourly_rate").value = profile.realized_hourly_rate;
    }
    if (profile.utilization_percent) {
      document.getElementById("utilization_percent").value = profile.utilization_percent;
    }
  }

  function syncPayMode() {
    const hourly = document.getElementById("employment_pay_mode").value === "hourly";
    document.getElementById("field-hourly-wage").hidden = !hourly;
    document.getElementById("field-annual-wages").hidden = hourly;
  }

  document.querySelectorAll("[data-next]").forEach(function (button) {
    button.addEventListener("click", function () {
      showStep(stepIndex + 1);
    });
  });
  document.querySelectorAll("[data-back]").forEach(function (button) {
    button.addEventListener("click", function () {
      showStep(stepIndex - 1);
    });
  });
  document.querySelectorAll("[data-step-target]").forEach(function (button) {
    button.addEventListener("click", function () {
      showStep(STEPS.indexOf(button.getAttribute("data-step-target")));
    });
  });
  document.getElementById("trade_profile").addEventListener("change", applyProfile);
  document.getElementById("employment_pay_mode").addEventListener("change", syncPayMode);
  document.getElementById("boa-recalculate").addEventListener("click", calculate);
  document.getElementById("boa-download-pdf").addEventListener("click", downloadPdf);
  document.getElementById("boa-start-over").addEventListener("click", startOver);
  syncPayMode();
  showStep(0);
})();
