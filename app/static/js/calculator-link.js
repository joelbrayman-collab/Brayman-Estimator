// Link to a project: saves a snapshot of the calculator's entries and result on a project.
const widgets = document.querySelectorAll("[data-link-project]");

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

widgets.forEach((widget) => {
  const select = widget.querySelector("[data-link-select]");
  if (!select) return;
  const button = widget.querySelector("[data-link-button]");
  const reference = widget.querySelector("[data-link-reference]");
  const status = widget.querySelector("[data-link-status]");
  const resultNode = () => document.querySelector(widget.dataset.result);
  const hasResult = () => {
    const node = resultNode();
    return Boolean(node && !node.hidden && node.innerText.trim() !== "");
  };
  const refresh = () => {
    button.disabled = !(select.value && hasResult());
  };
  const say = (html, isError) => {
    status.innerHTML = html;
    status.classList.toggle("error", Boolean(isError));
    status.hidden = false;
  };
  select.addEventListener("change", refresh);
  document.addEventListener("calculator:result", () => { status.hidden = true; refresh(); });
  document.addEventListener("calculator:cleared", refresh);
  const observed = resultNode();
  if (observed) new MutationObserver(refresh).observe(observed, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden"] });
  refresh();

  button.addEventListener("click", async () => {
    const node = resultNode();
    if (!node || !select.value) return;
    button.disabled = true;
    const text = node.innerText.trim();
    const summary = node.dataset.linkSummary || text.split("\n").map((line) => line.trim()).filter(Boolean).slice(0, 3).join(" · ");
    try {
      const response = await fetch(widget.dataset.endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || "",
        },
        body: JSON.stringify({
          calculator: widget.dataset.calculator,
          project_id: select.value,
          reference: reference ? reference.value : "",
          summary,
          entered: entered(document.querySelector(widget.dataset.form)),
          result_text: text,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.ok) {
        say(data.error || "The result could not be linked. Try again.", true);
      } else {
        const link = document.createElement("a");
        link.href = data.url;
        link.textContent = "Open the project";
        say(`Saved on ${data.project.replace(/[&<>]/g, "")}. `, false);
        status.append(link);
      }
    } catch (error) {
      say("The result could not be linked. Check the connection and try again.", true);
    }
    refresh();
  });
});
