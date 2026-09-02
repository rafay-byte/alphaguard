// AlphaGuard AI - Chart.js helpers, light premium styling
let __chartInstances = {};

function renderEquityChart(canvasId, equityData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (__chartInstances[canvasId]) __chartInstances[canvasId].destroy();

  const labels = equityData.map((_, i) => i + 1);
  __chartInstances[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Equity',
        data: equityData,
        borderColor: '#5b5fef',
        backgroundColor: 'rgba(91,95,239,0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2.5,
      }]
    },
    options: {
      responsive: true,
      animation: { duration: 700, easing: 'easeOutQuart' },
      plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
      scales: {
        x: { display: false },
        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#6b7280', font: { size: 11 } } }
      }
    }
  });
}
