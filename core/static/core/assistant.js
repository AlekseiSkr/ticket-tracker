// AI form assistant panel (templates/admin/change_form.html). It sends the question and the
// last field the user clicked into to /admin/assistant/. Answers go in as text, never HTML.
(() => {
  const root = document.querySelector(".assistant");
  if (!root) return;
  const panel = root.querySelector(".assistant-panel");
  const toggle = root.querySelector(".assistant-toggle");
  const question = panel.querySelector("textarea");
  const ask = panel.querySelector("button[type=submit]");
  const about = panel.querySelector(".assistant-field");
  const answer = panel.querySelector(".assistant-answer");
  let field = "";

  toggle.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", String(!panel.hidden));
    if (!panel.hidden) question.focus();
  });

  document.getElementById(root.dataset.form)?.addEventListener("focusin", (event) => {
    if (!event.target.name) return;
    field = event.target.name.replace(/^.*-\d+-/, ""); // inline inputs: "comments-0-body"
    const label = document.querySelector(`label[for="${CSS.escape(event.target.id)}"]`);
    about.textContent = `Asking about: ${(label?.textContent || field).replace("*", "").trim()}`;
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
          field,
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
