// Демоданные
const demoData = {
  stats: {students: 0, teams: 0, full: 0, incomplete: 0},
  correct: []
};

function loadDemo() {
  // обновляем статистику
  document.getElementById("totalStudents").textContent = demoData.stats.students;
  document.getElementById("totalTeams").textContent = demoData.stats.teams;
  document.getElementById("fullTeams").textContent = demoData.stats.full;
  document.getElementById("incompleteTeams").textContent = demoData.stats.incomplete;

  // заполняем таблицу
  fillTable("otherTable", demoData.other);
}

function fillTable(tableId, rows) {
  const tbody = document.getElementById(tableId).querySelector("tbody");
  tbody.innerHTML = "";
  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.time}</td><td>${r.members}</td><td>${r.project}</td>`;
    tbody.appendChild(tr);
  });
}

function refreshData() {
  alert("Обновление результатов (демо)");
  loadDemo();
}

window.onload = loadDemo;
