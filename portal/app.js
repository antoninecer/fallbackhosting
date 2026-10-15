"use strict";
const filter = document.getElementById("task-filter");
const result = document.getElementById("filter-result");
const rows = [...document.querySelectorAll("tbody tr[data-status]")];
filter.addEventListener("change", () => {
  let visible = 0;
  rows.forEach(row => {
    const status = row.dataset.status;
    const match = filter.value === "ALL" || status === filter.value ||
      (filter.value === "ACTIVE" && ["IN_PROGRESS", "TESTING"].includes(status));
    row.hidden = !match;
    if (match) visible++;
  });
  result.textContent = visible ? `Zobrazeno úkolů: ${visible}.` : "V této skupině zatím nejsou žádné úkoly.";
});
