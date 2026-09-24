const palette = {
  grid: "#232D3A",
  text: "#8592A3",
  accent: "#4C86B8",
  risk: "#C1443C",
};

Chart.defaults.color = palette.text;
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;

async function loadDashboard() {
  try {
    await fetchAndRender();
  } catch (err) {
    document.querySelector(".content").insertAdjacentHTML(
      "afterbegin",
      `<div class="error-box is-visible">Dashboard failed to load: ${err.message}</div>`
    );
  }
}

async function fetchAndRender() {
  const res = await fetch("/api/dashboard");
  const data = await res.json();

  if (data.error) {
    document.querySelector(".content").insertAdjacentHTML(
      "afterbegin",
      `<div class="error-box is-visible">${data.error}</div>`
    );
    return;
  }

  document.getElementById("kpi-total").textContent = data.totals.n_transactions;
  document.getElementById("kpi-flagged").textContent = data.totals.n_flagged;
  document.getElementById("kpi-avg").textContent = "$" + data.totals.avg_amount;
  document.getElementById("kpi-auc").textContent = data.metrics.roc_auc
    ? data.metrics.roc_auc.toFixed(3)
    : "n/a";

  const hourLabels = Object.keys(data.by_hour);
  const hourValues = Object.values(data.by_hour).map((v) => v * 100);
  new Chart(document.getElementById("chart-hour"), {
    type: "line",
    data: {
      labels: hourLabels,
      datasets: [
        {
          data: hourValues,
          borderColor: palette.accent,
          backgroundColor: "rgba(76,134,184,.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 0,
        },
      ],
    },
    options: baseOptions("% flagged"),
  });

  const typeLabels = Object.keys(data.by_type);
  const typeValues = Object.values(data.by_type).map((v) => v * 100);
  new Chart(document.getElementById("chart-type"), {
    type: "bar",
    data: {
      labels: typeLabels,
      datasets: [
        {
          data: typeValues,
          backgroundColor: palette.risk,
          borderRadius: 2,
          maxBarThickness: 34,
        },
      ],
    },
    options: baseOptions("% flagged"),
  });

  const amtLabels = Object.keys(data.by_amount);
  const amtValues = Object.values(data.by_amount).map((v) => v * 100);
  new Chart(document.getElementById("chart-amount"), {
    type: "bar",
    data: {
      labels: amtLabels,
      datasets: [
        {
          data: amtValues,
          backgroundColor: palette.accent,
          borderRadius: 2,
          maxBarThickness: 50,
        },
      ],
    },
    options: baseOptions("% flagged"),
  });
}

function baseOptions(yTitle) {
  return {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: palette.grid }, border: { color: palette.grid } },
      y: {
        grid: { color: palette.grid },
        border: { color: palette.grid },
        title: { display: true, text: yTitle, color: palette.text },
        beginAtZero: true,
      },
    },
  };
}

loadDashboard();
