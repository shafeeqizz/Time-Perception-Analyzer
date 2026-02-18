let trendChartInstance = null;
let scatterChartInstance = null;

let toastTimer = null;

function showToast(message, type = "success") {
  const el = document.getElementById("toast");
  if (!el) return;

  el.textContent = message;
  el.className = `toast show ${type}`;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.className = "toast";
  }, 2200);
}
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


async function loadSummary() {
  const data = await fetchJSON("/api/insights/summary");

  document.getElementById("summary-kpis").innerHTML = `
    <div class="kpi"><div class="label">Total entries</div><div class="value">${data.total_entries}</div></div>
    <div class="kpi"><div class="label">Avg % error</div><div class="value">${data.avg_percent_error}%</div></div>
    <div class="kpi"><div class="label">Overconfidence</div><div class="value">${data.overconfidence_index}%</div></div>
    <div class="kpi"><div class="label">Accuracy score</div><div class="value">${data.accuracy_score}</div></div>
  `;
}

async function loadTrends() {
  const data = await fetchJSON("/api/insights/trends");

  const labels = data.map(d => d.date);
  const values = data.map(d => Number(d.avg_percent_error));

  if (trendChartInstance) trendChartInstance.destroy();

  const ctx = document.getElementById("trendChart").getContext("2d");

  trendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Avg % Error",
        data: values,
        borderWidth: 2,
        tension: 0.25
      }]
    },
    options: {
      scales: {
        y: { ticks: { callback: v => v + "%" } }
      }
    }
  });
}

async function loadCorrelations() {
  const data = await fetchJSON("/api/insights/correlations");
  document.getElementById("correlation-data").innerHTML = `
    <p>Difficulty vs Error: ${data.difficulty_vs_error}</p>
    <p>Mood vs Error: ${data.mood_vs_error}</p>
    <p>Distractions vs Error: ${data.distractions_vs_error}</p>
  `;
}

async function loadEntries() {
  const data = await fetchJSON("/api/entries");

  const tbody = document.querySelector("#entries-table tbody");
  tbody.innerHTML = "";

  data.slice(0, 10).forEach(entry => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(entry.created_at).toLocaleDateString()}</td>
      <td>${entry.title}</td>
      <td>${entry.estimated_min}</td>
      <td>${entry.actual_min}</td>
      <td>${entry.difficulty}</td>
      <td>${entry.mood}</td>
      <td>${entry.distractions}</td>
    `;
    tbody.appendChild(row);
  });
}

async function loadScatter() {
  const data = await fetchJSON("/api/insights/scatter");
  const points = data.map(d => ({ x: d.difficulty, y: d.percent_error }));

  if (scatterChartInstance) scatterChartInstance.destroy();

  scatterChartInstance = new Chart(document.getElementById("scatterChart"), {
    type: "scatter",
    data: {
      datasets: [{
        label: "Difficulty vs % Error",
        data: points,
        pointRadius: 6,
        pointHoverRadius: 8,
        backgroundColor: "rgba(99, 179, 237, 0.9)",
        borderColor: "rgba(99, 179, 237, 1)"
      }]
    },
    options: {
      scales: {
        x: {
          title: { display: true, text: "Difficulty" },
          min: 1,
          max: 5,
          ticks: { stepSize: 1 },
          grid: { color: "#ffffff11" }
        },
        y: {
          title: { display: true, text: "% Error" },
          suggestedMin: -100,
          suggestedMax: 100,
          ticks: { callback: v => v + "%" },
          grid: {
            color: (context) => {
              if (context.tick && context.tick.value === 0) return "#ffffff88";
              return "#ffffff11";
            }
          }
        }
      },
      plugins: {
        legend: { labels: { color: "#e8eeff" } }
      }
    }
  });
}

async function loadRecommendations() {
  const data = await fetchJSON("/api/insights/recommendations");

  const list = document.getElementById("recommendations-list");
  list.innerHTML = "";

  data.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
}

function toInt(id) {
  const v = Number.parseInt(document.getElementById(id).value, 10);
  return Number.isFinite(v) ? v : null;
}

async function addEntry(event) {
  event.preventDefault();

  const btn = document.getElementById("submit-btn");
  const form = document.getElementById("entry-form");

  const payload = {
    title: document.getElementById("title").value.trim(),
    estimated_min: toInt("estimated"),
    actual_min: toInt("actual"),
    difficulty: toInt("difficulty"),
    mood: toInt("mood"),
    distractions: toInt("distractions"),
    category: null,
    notes: null
  };

  if (!payload.title || payload.estimated_min === null || payload.actual_min === null ||
      payload.difficulty === null || payload.mood === null || payload.distractions === null) {
    // even if toast is broken, this visible UI still helps
    btn.textContent = "Fix form errors";
    setTimeout(() => (btn.textContent = "Add entry"), 1200);
    return;
  }

  // lock UI
    btn.disabled = true;
    const prevText = btn.textContent;
    btn.textContent = "Adding…";

    const start = performance.now();

    try {
    const res = await fetch(`${API_BASE}/api/entries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
    }

    form.reset();
    await init();

    // ensure user sees "Adding..." at least 600ms
    const elapsed = performance.now() - start;
    if (elapsed < 600) await sleep(600 - elapsed);

    btn.textContent = "Added ✅";
    await sleep(800);
    btn.textContent = prevText;
    } catch (err) {
    console.error(err);

    const elapsed = performance.now() - start;
    if (elapsed < 600) await sleep(600 - elapsed);

    btn.textContent = "Failed ❌";
    await sleep(1200);
    btn.textContent = prevText;
    } finally {
    btn.disabled = false;
    }

}


async function init() {
  await loadSummary();
  await loadTrends();
  await loadCorrelations();
  await loadEntries();
  await loadScatter();
  await loadRecommendations();
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("entry-form").addEventListener("submit", addEntry);
  init();
});
