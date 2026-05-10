// Brew & Spice — Dashboard charts & heatmap

(function () {
  // ---- helpers --------------------------------------------------------------
  const json = id => JSON.parse(document.getElementById(id).textContent);

  const COFFEE  = '#d4a574';
  const ROAST   = '#b8855a';
  const CREAM   = '#f0c896';
  const GRID    = 'rgba(255,255,255,0.06)';
  const TICK    = '#9c8f82';
  const TEXT    = '#f3eee7';

  // Common Chart.js defaults
  Chart.defaults.color = TICK;
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.borderColor = GRID;

  // ---- data ----------------------------------------------------------------
  const weeklyLabels = json('weekly-labels');
  const weeklyData   = json('weekly-data');
  const hourlyLabels = json('hourly-labels');
  const hourlyData   = json('hourly-data');
  const revenueLabels= json('revenue-labels');
  const revenueData  = json('revenue-data');
  const topProdLabels= json('top-product-labels');
  const topProdData  = json('top-product-data');
  const heatmapData  = json('heatmap-data');

  // ---- 1. Weekly footfall (line) -------------------------------------------
  const wfCtx = document.getElementById('weeklyFootfallChart');
  if (wfCtx) {
    const grad = wfCtx.getContext('2d').createLinearGradient(0, 0, 0, 240);
    grad.addColorStop(0, 'rgba(212,165,116,0.35)');
    grad.addColorStop(1, 'rgba(212,165,116,0)');
    new Chart(wfCtx, {
      type: 'line',
      data: {
        labels: weeklyLabels,
        datasets: [{
          label: 'Visitors',
          data: weeklyData,
          borderColor: COFFEE,
          backgroundColor: grad,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: COFFEE,
          pointBorderColor: '#1a120c',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          borderWidth: 3,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: GRID, drawBorder: false } },
          y: { grid: { color: GRID, drawBorder: false }, beginAtZero: true,
               ticks: { precision: 0 } }
        }
      }
    });
  }

  // ---- 2. Hourly footfall (bar) — peak hour highlighted --------------------
  const hfCtx = document.getElementById('hourlyFootfallChart');
  if (hfCtx) {
    const max = Math.max(...hourlyData);
    const colors = hourlyData.map(v =>
      max > 0 && v === max ? COFFEE : 'rgba(184,133,90,0.55)');
    new Chart(hfCtx, {
      type: 'bar',
      data: {
        labels: hourlyLabels,
        datasets: [{
          label: 'Visitors',
          data: hourlyData,
          backgroundColor: colors,
          borderRadius: 4,
          maxBarThickness: 22,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: GRID }, ticks: { precision: 0 } }
        }
      }
    });
  }

  // ---- 3. Revenue trend (area line) ----------------------------------------
  const rvCtx = document.getElementById('revenueChart');
  if (rvCtx) {
    const grad = rvCtx.getContext('2d').createLinearGradient(0, 0, 0, 240);
    grad.addColorStop(0, 'rgba(108,194,141,0.35)');
    grad.addColorStop(1, 'rgba(108,194,141,0)');
    new Chart(rvCtx, {
      type: 'line',
      data: {
        labels: revenueLabels,
        datasets: [{
          label: 'Revenue (₹)',
          data: revenueData,
          borderColor: '#6cc28d',
          backgroundColor: grad,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          borderWidth: 2.5,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: { label: ctx => '₹' + Number(ctx.parsed.y).toLocaleString('en-IN') }
          }
        },
        scales: {
          x: { grid: { color: GRID } },
          y: { beginAtZero: true, grid: { color: GRID },
               ticks: { callback: v => '₹' + v } }
        }
      }
    });
  }

  // ---- 4. Top products (horizontal bar) ------------------------------------
  const tpCtx = document.getElementById('topProductsChart');
  if (tpCtx) {
    new Chart(tpCtx, {
      type: 'bar',
      data: {
        labels: topProdLabels,
        datasets: [{
          label: 'Units sold',
          data: topProdData,
          backgroundColor: [COFFEE, ROAST, CREAM, '#a16f4d', '#c79774', '#8d6242'],
          borderRadius: 5,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: GRID }, ticks: { precision: 0 } },
          y: { grid: { display: false } }
        }
      }
    });
  }

  // ---- 5. Heatmap (7 days × 24 hours) --------------------------------------
  const heat = document.getElementById('heatmap');
  if (heat) {
    // find global max for color scaling
    let max = 0;
    heatmapData.forEach(row => row.forEach(v => { if (v > max) max = v; }));
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    let html = '<div class="hm-label"></div>'; // top-left blank
    for (let h = 0; h < 24; h++) {
      // show every 2 hours to save space
      html += `<div class="hm-head">${h % 2 === 0 ? h.toString().padStart(2,'0') : ''}</div>`;
    }
    for (let d = 0; d < 7; d++) {
      html += `<div class="hm-label">${days[d]}</div>`;
      for (let h = 0; h < 24; h++) {
        const v = heatmapData[d][h];
        const intensity = max > 0 ? v / max : 0;
        // base color = coffee, alpha by intensity
        const alpha = intensity === 0 ? 0.04 : 0.15 + intensity * 0.75;
        const bg = `rgba(212,165,116,${alpha.toFixed(2)})`;
        html += `<div class="hm-cell" style="background:${bg}" title="${days[d]} ${h}:00 — ${v} visitors"></div>`;
      }
    }
    heat.innerHTML = html;
  }

  // ---- 6. Live KPI poll (every 30s) ---------------------------------------
  const ffEl  = document.getElementById('kpi-footfall');
  const revEl = document.getElementById('kpi-revenue');
  if (ffEl && revEl) {
    setInterval(async () => {
      try {
        const r = await fetch('/api/today-stats/');
        if (!r.ok) return;
        const d = await r.json();
        ffEl.textContent  = d.footfall;
        revEl.textContent = Math.round(d.revenue).toLocaleString('en-IN');
      } catch (_) { /* offline; ignore */ }
    }, 30000);
  }
})();
