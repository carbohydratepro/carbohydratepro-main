(() => {
  const canvas = document.getElementById('security-chart') as HTMLCanvasElement | null;
  const element = document.getElementById('security-chart-data');
  if (!canvas || !element) return;
  const rows = JSON.parse(element.textContent || '[]') as Array<{
    date: string; critical: number | null; error: number | null;
    warning: number | null; maintenance: number | null;
  }>;
  const knownRows = rows.filter(row => row.critical !== null);
  const context = canvas.getContext('2d');
  if (!context) return;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  new Chart(context, {
    type: 'bar',
    data: {
      labels: knownRows.map(row => row.date.slice(5)),
      datasets: [
        { label: '重大', data: knownRows.map(row => row.critical ?? 0), backgroundColor: '#bd2635' },
        { label: 'エラー', data: knownRows.map(row => row.error ?? 0), backgroundColor: '#bc6500' },
        { label: '警告・拒否', data: knownRows.map(row => row.warning ?? 0), backgroundColor: '#4169a1' },
        { label: '予定メンテナンス', data: knownRows.map(row => row.maintenance ?? 0), backgroundColor: '#7b858e' },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, animation: reducedMotion ? false : undefined,
      scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
})();
