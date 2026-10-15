"use strict";
const filter = document.getElementById("task-filter");
const result = document.getElementById("filter-result");
const tasks = [...document.querySelectorAll(".task[data-status]")];
filter.addEventListener("change", () => {
  let count = 0;
  tasks.forEach(task => {
    const status = task.dataset.status;
    const visible = filter.value === "ALL" || filter.value === status ||
      (filter.value === "ACTIVE" && ["IN_PROGRESS", "TESTING"].includes(status));
    task.hidden = !visible;
    if (visible) count++;
  });
  result.textContent = count ? `Zobrazeno úkolů: ${count}.` : "V této skupině nejsou žádné úkoly.";
});
document.getElementById("copy-resume").addEventListener("click", async () => {
  const prompt = document.getElementById("resume-prompt");
  const status = document.getElementById("copy-result");
  try {
    await navigator.clipboard.writeText(prompt.value);
    status.textContent = "Podklad byl zkopírován. Před pokračováním ověřte skutečný stav.";
  } catch {
    prompt.focus();
    prompt.select();
    status.textContent = "Automatické kopírování není dostupné. Označený text zkopírujte ručně nebo stáhněte TXT.";
  }
});
