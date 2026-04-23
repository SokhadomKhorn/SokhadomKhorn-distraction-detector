const ctx = document.getElementById('alertsChart');

if (ctx && window.analyticsData) {
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: window.analyticsData.labels,
      datasets: [{
        label: 'Alerts',
        data: window.analyticsData.counts,
        borderWidth: 0,
        borderRadius: 10,
        backgroundColor: 'rgba(56, 189, 248, 0.85)',
        hoverBackgroundColor: 'rgba(34, 197, 94, 0.9)'
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#94a3b8'
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#94a3b8',
            precision: 0
          },
          grid: {
            color: 'rgba(148, 163, 184, 0.12)'
          }
        }
      }
    }
  });
}