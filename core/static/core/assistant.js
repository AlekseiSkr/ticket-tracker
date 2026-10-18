// AI form assistant panel (templates/admin/change_form.html). Sends the question and the chosen
// field to /admin/assistant/ and shows the answer as text, never HTML.
(() => {
  const root = document.querySelector(".assistant");
  if (!root) return;
  const panel = root.querySelector(".assistant-panel");
  const toggle = root.querySelector(".assistant-toggle");
  const fieldSelect = panel.querySelector("#assistant-field");
  const question = panel.querySelector("textarea");
  const ask = panel.querySelector("button[type=submit]");
  const answer = panel.querySelector(".assistant-answer");

  toggle.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", String(!panel.hidden));
    if (!panel.hidden) question.focus();
  });

  // Focusing a field preselects it. Searchable dropdowns focus a widget placed right after
  // their real <select>, so take the name from there. Disabled and read-only fields can't be
  // focused; the list still offers them.
  document.getElementById(root.dataset.form)?.addEventListener("focusin", (event) => {
    const input = event.target.name ? event.target : event.target.closest(".select2")?.previousElementSibling;
    const name = input?.name?.replace(/^.*-\d+-/, ""); // inline inputs are named "comments-0-body"
    if (name && fieldSelect.querySelector(`option[value="${CSS.escape(name)}"]`)) fieldSelect.value = name;
  });

  question.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      panel.requestSubmit();
    }
  });

  panel.addEventListener("submit", async (event) => {
    event.preventDefault();
    ask.disabled = true;
    answer.textContent = "Thinking…";
    try {
      const response = await fetch(root.dataset.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": panel.querySelector("[name=csrfmiddlewaretoken]").value,
        },
        body: JSON.stringify({
          app_label: root.dataset.appLabel,
          model_name: root.dataset.modelName,
          object_id: root.dataset.objectId || null,
          field: fieldSelect.value,
          question: question.value,
        }),
      });
      const data = await response.json();
      answer.textContent = data.answer || data.error;
    } catch {
      answer.textContent = "The assistant isn't reachable. Each field's help text is below it.";
    } finally {
      ask.disabled = false;
    }
  });
})();
