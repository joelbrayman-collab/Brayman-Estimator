// After a calculator result (Guided Estimating, 23 Oct 2026): Use Result Only, Add to Existing Project, or
// Create New Project. "Add to Existing Project" is the "Link to a project" record (23 Oct 2026), now carrying the
// calculator's Contract V1 result and an optional estimating stage. Nothing here changes an estimate: the result
// reaches an estimate only through the estimate review, where a person confirms each quantity.
const panels = document.querySelectorAll("[data-result-options]");

function labelFor(control) {
  if (control.id) {
    const label = document.querySelector(`label[for="${CSS.escape(control.id)}"]`);
    if (label) {
      const first = label.querySelector("span, strong");
      return (first ? first.textContent : label.textContent).trim();
    }
  }
  const wrapping = control.closest("label");
  if (wrapping) return wrapping.textContent.replace(control.value || "", "").trim().split("\n")[0].trim();
  return control.name || "";
}

function unitFor(control) {
  const wrap = control.closest(".cc-input");
  const unit = wrap ? wrap.querySelector("strong") : null;
  return unit ? ` ${unit.textContent.trim()}` : "";
}

function entered(form) {
  if (!form) return [];
  const rows = [];
  const seenGroups = new Set();
  form.querySelectorAll("input, select, textarea").forEach((control) => {
    if (control.type === "hidden" || control.type === "submit" || control.type === "button") return;
    if (control.closest("[hidden]")) return;
    if (control.name === "csrf_token") return;
    if (control.type === "radio") {
      if (seenGroups.has(control.name)) return;
      seenGroups.add(control.name);
      const checked = form.querySelector(`input[name="${CSS.escape(control.name)}"]:checked`);
      if (!checked) return;
      const legend = control.closest("fieldset")?.querySelector("legend");
      const label = document.querySelector(`label[for="${CSS.escape(checked.id)}"]`);
      const value = label ? (label.querySelector("strong") || label).textContent.trim() : checked.value;
      rows.push({ label: legend ? legend.textContent.trim() : control.name, value });
      return;
    }
    if (control.type === "checkbox") {
      rows.push({ label: labelFor(control), value: control.checked ? "Yes" : "No" });
      return;
    }
    const value = control.tagName === "SELECT" ? control.selectedOptions[0]?.textContent.trim() : control.value.trim();
    if (value) rows.push({ label: labelFor(control), value: value + (control.tagName === "SELECT" ? "" : unitFor(control)) });
  });
  return rows;
}

// Every field's value, so "Create New Project" → Cancel can show the same result again.
function formState(form) {
  if (!form) return [];
  if ((form.getAttribute("method") || "get").toLowerCase() === "post") {
    // A server calculator: the exact fields it was posted with (every row), sent again on the way back.
    const pairs = [];
    for (const [name, value] of new FormData(form).entries()) {
      if (name !== "csrf_token" && typeof value === "string") pairs.push([`post:${name}`, value]);
    }
    return pairs;
  }
  const state = [];
  form.querySelectorAll("input, select, textarea").forEach((control, index) => {
    if (control.type === "submit" || control.type === "button" || control.type === "file") return;
    if (control.name === "csrf_token") return;
    const key = control.name ? `name:${control.name}:${index}` : control.id ? `id:${control.id}` : `index:${index}`;
    if (control.type === "radio" || control.type === "checkbox") {
      state.push([key, control.checked ? "1" : ""]);
    } else {
      state.push([key, control.value]);
    }
  });
  return state;
}

function setNative(control, value) {
  const proto = control.tagName === "SELECT" ? HTMLSelectElement.prototype
    : control.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
  if (setter) setter.call(control, value); else control.value = value;
}

function restore(form, state) {
  const controls = Array.from(form.querySelectorAll("input, select, textarea"));
  // Rows added by "add another" buttons are not present yet; the server pages already render enough rows.
  for (const [key, value] of state) {
    let control = null;
    if (key.startsWith("id:")) control = document.getElementById(key.slice(3));
    else if (key.startsWith("name:")) {
      const parts = key.split(":");
      const index = Number(parts[parts.length - 1]);
      control = controls[index] && controls[index].name === parts.slice(1, -1).join(":") ? controls[index] : null;
    } else if (key.startsWith("index:")) control = controls[Number(key.slice(6))] || null;
    if (!control) continue;
    if (control.type === "radio" || control.type === "checkbox") {
      if (Boolean(value) !== control.checked) control.click();
    } else {
      setNative(control, value);
      control.dispatchEvent(new Event("input", { bubbles: true }));
      control.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }
}

function csrf() {
  return document.querySelector('meta[name="csrf-token"]')?.content
    || document.querySelector("[data-result-options]")?.dataset.csrf || "";
}

function contractFor(resultNode, panel) {
  if (resultNode && resultNode.dataset.contract) {
    try { return JSON.parse(resultNode.dataset.contract); } catch (error) { return null; }
  }
  const script = panel.querySelector("[data-calculator-contract]");
  if (script) {
    try { return JSON.parse(script.textContent); } catch (error) { return null; }
  }
  return null;
}

panels.forEach((panel) => {
  const resultNode = () => document.querySelector(panel.dataset.result);
  const formNode = () => document.querySelector(panel.dataset.form);
  const hasResult = () => {
    const node = resultNode();
    return Boolean(node && !node.hidden && node.innerText.trim() !== "");
  };
  const summaryOf = (node) => node.dataset.linkSummary || node.innerText.trim().split("\n").map((l) => l.trim()).filter(Boolean).slice(0, 3).join(" · ");

  // Restore after "Create New Project" → Cancel: the same entries, calculated again by the same engine.
  const saved = panel.querySelector("[data-carry-form-state]");
  // The server sends the saved entries only on the first (GET) page, so this runs once per return.
  if (saved && formNode()) {
    const state = JSON.parse(saved.textContent || "[]");
    const form = formNode();
    // After every script on the page is running (the calculator's own engine listens for its form's submit).
    const run = () => {
      restore(form, state);
      const button = form.querySelector('button[type="submit"], [data-calculate], button:not([type])');
      if (button) button.click(); else form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    };
    if (document.readyState === "complete") run(); else window.addEventListener("load", run, { once: true });
  }

  // A: use the result only.
  const useOnly = panel.querySelector("[data-use-result-only]");
  useOnly?.addEventListener("click", () => {
    panel.querySelector("[data-a-status]").hidden = false;
  });

  // B: add to an existing project (and, optionally, one of its estimating stages).
  const widget = panel.querySelector("[data-link-project]");
  const select = widget?.querySelector("[data-link-select]");
  const button = widget?.querySelector("[data-link-button]");
  const stageWrap = widget?.querySelector("[data-stage-wrap]");
  const stageSelect = widget?.querySelector("[data-link-stage]");
  const reference = widget?.querySelector("[data-link-reference]");
  const status = widget?.querySelector("[data-link-status]");
  const newProject = panel.querySelector("[data-new-project-button]");
  const cStatus = panel.querySelector("[data-c-status]");
  let busy = false;
  const refresh = () => {
    if (button) button.disabled = busy || !(select && select.value && hasResult());
    if (newProject) newProject.disabled = busy || !hasResult();
  };
  const say = (node, html, isError) => {
    node.innerHTML = html;
    node.classList.toggle("error", Boolean(isError));
    node.hidden = false;
  };
  const loadStages = async () => {
    if (!stageSelect || !select) return;
    stageSelect.innerHTML = '<option value="">No stage</option>';
    stageWrap.hidden = true;
    if (!select.value) return;
    try {
      const response = await fetch(panel.dataset.stagesEndpoint + select.value, { headers: { Accept: "application/json" } });
      const data = await response.json();
      if (!response.ok || !data.ok) return;
      for (const [id, label] of data.stages) {
        const option = document.createElement("option");
        option.value = String(id);
        option.textContent = label;
        if (String(id) === widget.dataset.preselectStage) option.selected = true;
        stageSelect.append(option);
      }
      stageWrap.hidden = data.stages.length === 0;
    } catch (error) { /* stages are optional */ }
  };
  select?.addEventListener("change", () => { refresh(); loadStages(); });
  document.addEventListener("calculator:result", () => { if (status) status.hidden = true; refresh(); });
  document.addEventListener("calculator:cleared", refresh);
  const observed = resultNode();
  if (observed) new MutationObserver(refresh).observe(observed, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden"] });
  refresh();
  if (select && select.value) loadStages();

  button?.addEventListener("click", async () => {
    const node = resultNode();
    if (!node || !select.value || busy) return;
    busy = true;
    refresh();
    const text = node.innerText.trim();
    try {
      const response = await fetch(widget.dataset.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({
          calculator: widget.dataset.calculator,
          project_id: select.value,
          stage_id: stageSelect && stageSelect.value ? stageSelect.value : null,
          reference: reference ? reference.value : "",
          summary: summaryOf(node),
          entered: entered(formNode()),
          result_text: text,
          payload: contractFor(node, panel),
          source: location.pathname.startsWith("/useful-calculators/") ? "USEFUL_CALCULATORS" : "CALCULATORS",
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.ok) {
        say(status, data.error || "The result could not be linked. Try again.", true);
      } else {
        const project = String(data.project).replace(/[&<>]/g, "");
        say(status, data.created ? `Saved on ${project}. ` : `Already on ${project}; it was not added twice. `, false);
        const link = document.createElement("a");
        link.href = data.review_url || data.url;
        link.dataset.linkOpen = "1";
        link.textContent = data.review_url ? "Review it for the estimate" : "Open the project";
        status.append(link);
      }
    } catch (error) {
      say(status, "The result could not be linked. Check the connection and try again.", true);
    }
    busy = false;
    refresh();
  });

  // C: create a new project with this result.
  newProject?.addEventListener("click", async () => {
    const node = resultNode();
    if (!node || busy) return;
    busy = true;
    refresh();
    try {
      const response = await fetch(panel.dataset.carryEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({
          calculator: panel.dataset.calculator,
          summary: summaryOf(node),
          entered: entered(formNode()),
          result_text: node.innerText.trim(),
          payload: contractFor(node, panel),
          form_state: formState(formNode()),
          return_path: panel.dataset.returnPath,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.ok) {
        say(cStatus, data.error || "The new project could not be started. Try again.", true);
        busy = false;
        refresh();
        return;
      }
      location.assign(data.url);
    } catch (error) {
      say(cStatus, "The new project could not be started. Check the connection and try again.", true);
      busy = false;
      refresh();
    }
  });
});
