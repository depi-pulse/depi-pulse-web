// DEPI Pulse — small client helpers: theme, ECharts from server data, toasts.
window.DP = (() => {
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const dark = () => document.documentElement.dataset.theme === 'dark';
  const ar = v => new Intl.NumberFormat('ar-EG').format(v);
  const charts = [];

  function toggleTheme() {
    const r = document.documentElement;
    r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('dp-theme', r.dataset.theme); } catch (e) {}
    drawAll();
  }

  function base() {
    const line = css('--line'), t3 = css('--text-3');
    return {
      textStyle: { fontFamily: 'Readex Pro, Alexandria, sans-serif', color: css('--text-2') },
      color: [dark() ? css('--primary') : css('--eb-500'), css('--ochre-500'), css('--tr-dat'), css('--tr-drt'), css('--tr-ais'), css('--tr-iss'), css('--tr-ind'), css('--tr-gam')],
      grid: { top: 26, right: 12, bottom: 26, left: 12, containLabel: true },
      tooltip: { backgroundColor: css('--text'), borderWidth: 0, textStyle: { color: css('--surface'), fontFamily: 'Readex Pro' },
        extraCssText: 'border-radius:10px;direction:rtl;text-align:right' },
      ax: { axisLine: { lineStyle: { color: line } }, axisTick: { show: false }, axisLabel: { color: t3, fontSize: 11.5 }, splitLine: { lineStyle: { color: line, type: [3, 4] } } },
    };
  }

  function option(spec) {
    const b = base(), ax = b.ax; delete b.ax;
    const fmt = v => ar(v) + (spec.unit || '');
    if (spec.type === 'pie') {
      return { ...b, tooltip: { ...b.tooltip, trigger: 'item', valueFormatter: fmt }, legend: { bottom: 0, textStyle: { color: css('--text-2') } },
        series: [{ type: 'pie', radius: ['52%', '78%'], center: ['50%', '45%'], itemStyle: { borderColor: css('--surface'), borderWidth: 2, borderRadius: 6 },
          label: { show: false }, data: spec.labels.map((l, i) => ({ name: l, value: spec.values[i] })) }] };
    }
    if (spec.type === 'stack') {
      return { ...b, tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: fmt }, legend: { top: 0, textStyle: { color: css('--text-2') } },
        grid: { ...b.grid, top: 36 },
        xAxis: { ...ax, type: 'value', inverse: true, axisLabel: { ...ax.axisLabel, formatter: ar } },
        yAxis: { ...ax, type: 'category', data: spec.labels, inverse: true, position: 'right', axisLine: { show: false } },
        series: spec.series.map((s, i) => ({ name: s.name, type: 'bar', stack: 't', barWidth: 14, data: s.values,
          itemStyle: i === 0 ? { color: p => spec.colors ? spec.colors[p.dataIndex] : css('--primary'), borderRadius: [0, 0, 0, 0] } : { color: css('--surface-3') } })) };
    }
    const horizontal = !!spec.horizontal;
    const cat = { ...ax, type: 'category', data: spec.labels, inverse: true };
    const val = { ...ax, type: 'value', axisLabel: { ...ax.axisLabel, formatter: fmt }, min: spec.min };
    if (horizontal) { cat.position = 'right'; cat.axisLine = { show: false }; val.inverse = true; } else { val.position = 'right'; val.axisLine = { show: false }; }
    const series = { type: spec.type === 'line' ? 'line' : 'bar', data: spec.values, barMaxWidth: 26, smooth: .35, symbolSize: 6,
      itemStyle: { color: css('--primary'), borderRadius: horizontal ? [6, 0, 0, 6] : [6, 6, 0, 0] },
      label: horizontal ? { show: true, position: 'left', formatter: p => ar(p.value), color: css('--text-2'), fontSize: 11.5 } : undefined,
      areaStyle: spec.type === 'line' ? { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: css('--primary') + '44' }, { offset: 1, color: css('--primary') + '00' }]) } : undefined };
    return { ...b, tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: fmt }, xAxis: horizontal ? val : cat, yAxis: horizontal ? cat : val, series: [series] };
  }

  function drawAll() {
    if (!window.echarts) return;
    charts.forEach(c => c.dispose()); charts.length = 0;
    document.querySelectorAll('[data-chart]').forEach(el => {
      const src = document.getElementById(el.dataset.chart); if (!src) return;
      const c = echarts.init(el, null, { renderer: 'canvas' });
      c.setOption(option(JSON.parse(src.textContent)));
      charts.push(c);
    });
  }
  addEventListener('resize', () => charts.forEach(c => c.resize()));
  addEventListener('DOMContentLoaded', () => { drawAll(); document.body.addEventListener('htmx:afterSwap', () => { const t = document.getElementById('thread'); if (t) t.scrollTop = t.scrollHeight; }); });

  function toast(title, sub = '') {
    let box = document.querySelector('.toasts');
    if (!box) { box = document.body.appendChild(document.createElement('div')); box.className = 'toasts'; }
    const t = document.createElement('div'); t.className = 'toast ok'; t.innerHTML = `<div><b>${title}</b>${sub ? `<small>${sub}</small>` : ''}</div>`;
    box.appendChild(t); setTimeout(() => t.remove(), 3800);
  }
  return { toggleTheme, drawAll, toast };
})();
