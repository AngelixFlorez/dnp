// ============================================================
//  app.js — Dashboard IDF · Departamento Nacional de Planeación
//  Compatible con la nueva estructura de sidebar + secciones.
// ============================================================

// === Configuration ===
const DATA_URL = './datos_idf.json';
const SVG_URL  = 'colombia_dep.svg';

// === State ===
let idfData         = null;
let currentZoom     = 1;
let panX            = 0;
let panY            = 0;
let isPanning       = false;
let panStart        = { x: 0, y: 0 };

// === DOM refs ===
const yearSelect       = document.getElementById('yearSelect');
const deptSelect       = document.getElementById('deptSelect');
const svgContainer     = document.getElementById('svgMapContainer');
const deptNameEl       = document.getElementById('deptName');
const histDeptNameEl   = document.getElementById('histDeptName');
const tooltipEl        = document.getElementById('mapTooltip');

// === IDF colour / range helpers ===
const IDF_COLORS = {
  deterioro:  '#ff7f7f',
  riesgo:     '#ffb84d',
  vulnerable: '#ffea7f',
  solvente:   '#95e080',
  sostenible: '#28a745'
};
const IDF_RANGES = [
  { key: 'deterioro',  label: 'Deterioro (<40)',     min: 0,  max: 40  },
  { key: 'riesgo',     label: 'Riesgo (40–<60)',     min: 40, max: 60  },
  { key: 'vulnerable', label: 'Vulnerable (60–<70)', min: 60, max: 70  },
  { key: 'solvente',   label: 'Solvente (70–<80)',   min: 70, max: 80  },
  { key: 'sostenible', label: 'Sostenible (≥80)',    min: 80, max: 101 }
];

function getIdfColor(score) {
  if (score < 40) return IDF_COLORS.deterioro;
  if (score < 60) return IDF_COLORS.riesgo;
  if (score < 70) return IDF_COLORS.vulnerable;
  if (score < 80) return IDF_COLORS.solvente;
  return IDF_COLORS.sostenible;
}
function getIdfRangeKey(score) {
  if (score < 40) return 'deterioro';
  if (score < 60) return 'riesgo';
  if (score < 70) return 'vulnerable';
  if (score < 80) return 'solvente';
  return 'sostenible';
}
function rangoBadgeClass(rango) {
  const m = { Deterioro:'deterioro', Riesgo:'riesgo', Vulnerable:'vulnerable', Solvente:'solvente', Sostenible:'sostenible' };
  return m[rango] || 'riesgo';
}
function getRangoLabel(rango) {
  const m = {
    'Deterioro': 'Deterioro (<40)',
    'Riesgo':    'Riesgo (≥40 y <60)',
    'Vulnerable':'Vulnerable (≥60 y <70)',
    'Solvente':  'Solvente (≥70 y <80)',
    'Sostenible':'Sostenible (≥80)',
    'N/A':       'N/A'
  };
  return m[rango] || rango || 'N/A';
}

// === SVG id → dept name ===
const idToDept = {
  'CO-AMA':'AMAZONAS',         'CO-ANT':'ANTIOQUIA',          'CO-ARA':'ARAUCA',
  'CO-ATL':'ATLANTICO',        'CO-BOL':'BOLIVAR',            'CO-BOY':'BOYACA',
  'CO-CAL':'CALDAS',           'CO-CAQ':'CAQUETA',            'CO-CAS':'CASANARE',
  'CO-CAU':'CAUCA',            'CO-CES':'CESAR',              'CO-CHO':'CHOCO',
  'CO-COR':'CORDOBA',          'CO-CUN':'CUNDINAMARCA',       'CO-DC': 'BOGOTA D.C.',
  'CO-GUA':'GUAINIA',          'CO-GUV':'GUAVIARE',           'CO-HUI':'HUILA',
  'CO-LAG':'GUAJIRA',          'CO-MAG':'MAGDALENA',          'CO-MET':'META',
  'CO-NAR':'NARIÑO',           'CO-NSA':'NORTE DE SANTANDER', 'CO-PUT':'PUTUMAYO',
  'CO-QUI':'QUINDIO',          'CO-RIS':'RISARALDA',          'CO-SAN':'SANTANDER',
  'CO-SAP':'SAN ANDRÉS',       'CO-SUC':'SUCRE',              'CO-TOL':'TOLIMA',
  'CO-VAC':'VALLE DEL CAUCA',  'CO-VAU':'VAUPES',             'CO-VID':'VICHADA'
};
function mapIdToDeptName(id) {
  return idToDept[id] || id.replace('CO-','').replace(/_/g,' ').toUpperCase();
}

// === KPI elements (all data-key attrs across the page) ===
function getKpi(key) { return document.querySelector(`[data-key="${key}"]`); }

// === Chart instances ===
let historicalChart   = null;
let nationalAvgChart  = null;
let nationalDistChart = null;
let top10Chart        = null;
let tipologiaChart    = null;
let categoriaChart    = null;

// ============================================================
//  INIT
// ============================================================
async function init() {
  try {
    const [dataResp, svgResp] = await Promise.all([
      fetch(DATA_URL),
      fetch(SVG_URL)
    ]);
    if (!dataResp.ok) throw new Error('JSON ' + dataResp.status);
    if (!svgResp.ok)  throw new Error('SVG '  + svgResp.status);

    const rawData = await dataResp.json();
    idfData = {
      years:       rawData.meta.anios,
      departments: rawData.meta.departamentos,
      byYear:      rawData.records
    };

    injectSvg(await svgResp.text());
    populateYearSelector();
    populateDeptSelector();
    attachEventHandlers();
    setupZoomControls();
    setupPanControls();
    setupSidebarNav();

    updateDashboard(yearSelect.value, deptSelect.value);
  } catch (err) {
    console.error('Init error:', err);
    const msg = document.createElement('div');
    msg.style.cssText = 'position:fixed;top:12px;right:12px;background:#fee2e2;color:#991b1b;padding:12px 16px;border:1px solid #fca5a5;border-radius:8px;z-index:9999;font-size:0.85rem;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.15)';
    msg.textContent = '⚠ Error al cargar datos. Usa un servidor HTTP local (p.ej. Live Server).';
    document.body.appendChild(msg);
  }
}

// ============================================================
//  SIDEBAR NAVIGATION
// ============================================================
function setupSidebarNav() {
  document.querySelectorAll('.nav-btn[data-section]').forEach(btn => {
    btn.addEventListener('click', () => {
      const sectionId = btn.dataset.section;

      // Update active button
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Show / hide sections
      document.querySelectorAll('.dash-section').forEach(s => s.classList.remove('active'));
      const target = document.getElementById('section-' + sectionId);
      if (target) target.classList.add('active');

      // Resize charts that may have been hidden (Chart.js needs visible canvas)
      setTimeout(() => resizeAllCharts(), 50);
    });
  });
}

function resizeAllCharts() {
  [historicalChart, nationalAvgChart, nationalDistChart,
   top10Chart, tipologiaChart, categoriaChart].forEach(c => {
    if (c) c.resize();
  });
}

// ============================================================
//  SVG MAP
// ============================================================
function injectSvg(svgContent) {
  svgContainer.innerHTML = svgContent;
  const svg = svgContainer.querySelector('svg');
  if (!svg) return;
  svg.removeAttribute('width');
  svg.removeAttribute('height');
  svg.setAttribute('viewBox', '0 0 612.82 693.68');
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.style.width  = '100%';
  svg.style.height = '100%';
  svg.id = 'colombiaSvg';

  svg.querySelectorAll('path').forEach(path => {
    const deptId = path.id;
    if (deptId === 'CO-DC') {
      path.addEventListener('mouseenter', e => showTooltip(e, 'Bogotá D.C.\n(No aplica)'));
      path.addEventListener('mousemove',  e => moveTooltip(e));
      path.addEventListener('mouseleave', hideTooltip);
      return;
    }
    const deptName = mapIdToDeptName(deptId);
    path.addEventListener('mouseenter', e => {
      const score = getDeptScore(yearSelect.value, deptName);
      showTooltip(e, `${deptName}\nIDF: ${score !== undefined ? score.toFixed(2) : 'N/A'}`);
    });
    path.addEventListener('mousemove',  e => moveTooltip(e));
    path.addEventListener('mouseleave', hideTooltip);
    path.addEventListener('click', () => {
      deptSelect.value = deptName;
      updateDashboard(yearSelect.value, deptName);
    });
  });
}

function highlightDeptOnMap(deptName) {
  const svg = svgContainer.querySelector('svg');
  if (!svg) return;
  svg.querySelectorAll('path').forEach(p => p.classList.remove('selected-dept'));
  if (!deptName || deptName === 'BOGOTA D.C.') return;
  const entry = Object.entries(idToDept).find(([, v]) => v === deptName);
  if (entry) {
    const el = svg.getElementById(entry[0]);
    if (el) el.classList.add('selected-dept');
  }
}

function getDeptScore(year, deptName) {
  const yd = idfData.byYear[year];
  if (!yd) return undefined;
  const d = yd[deptName];
  return d ? d.idf : undefined;
}

// ============================================================
//  ZOOM & PAN
// ============================================================
function setupZoomControls() {
  document.getElementById('zoomIn').addEventListener('click', () => {
    currentZoom = Math.min(5, currentZoom * 1.3); applyZoom();
  });
  document.getElementById('zoomOut').addEventListener('click', () => {
    currentZoom = Math.max(0.3, currentZoom / 1.3); applyZoom();
  });
  document.getElementById('zoomReset').addEventListener('click', () => {
    currentZoom = 1; panX = 0; panY = 0; applyZoom();
  });
}
function applyZoom() {
  const svg = svgContainer.querySelector('svg');
  if (!svg) return;
  svg.style.transform       = `translate(${panX}px, ${panY}px) scale(${currentZoom})`;
  svg.style.transformOrigin = '0 0';
}
function setupPanControls() {
  svgContainer.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    isPanning = true;
    panStart  = { x: e.clientX, y: e.clientY };
    document.body.style.cursor = 'grabbing';
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!isPanning) return;
    panX += e.clientX - panStart.x;
    panY += e.clientY - panStart.y;
    panStart = { x: e.clientX, y: e.clientY };
    applyZoom();
  });
  document.addEventListener('mouseup', () => {
    if (isPanning) { isPanning = false; document.body.style.cursor = ''; }
  });
}

// ============================================================
//  TOOLTIP
// ============================================================
function showTooltip(e, text) {
  tooltipEl.textContent = text;
  tooltipEl.style.display = 'block';
  moveTooltip(e);
}
function moveTooltip(e) {
  tooltipEl.style.left = (e.clientX + 14) + 'px';
  tooltipEl.style.top  = (e.clientY - 10) + 'px';
}
function hideTooltip() { tooltipEl.style.display = 'none'; }

// ============================================================
//  SELECTORS
// ============================================================
function populateYearSelector() {
  idfData.years.forEach(y => {
    const o = document.createElement('option');
    o.value = y; o.textContent = y;
    yearSelect.appendChild(o);
  });
  yearSelect.value = idfData.years[idfData.years.length - 1];
}
function populateDeptSelector() {
  idfData.departments.forEach(d => {
    const o = document.createElement('option');
    o.value = d; o.textContent = d;
    deptSelect.appendChild(o);
  });
  deptSelect.value = idfData.departments[0];
}
function attachEventHandlers() {
  yearSelect.addEventListener('change', () => updateDashboard(yearSelect.value, deptSelect.value));
  deptSelect.addEventListener('change', () => updateDashboard(yearSelect.value, deptSelect.value));
}

// ============================================================
//  MAIN UPDATE
// ============================================================
function updateDashboard(year, dept) {
  if (!idfData) return;
  const yearData    = idfData.byYear[year];
  if (!yearData) return;
  const priorYear   = String(parseInt(year) - 1);
  const priorYearData = idfData.byYear[priorYear] || {};

  // Map highlight
  highlightDeptOnMap(dept);

  // KPIs
  const allScores   = Object.values(yearData).map(d => d.idf).filter(v => v != null);
  const nationalAvg = allScores.length ? allScores.reduce((a,b)=>a+b,0)/allScores.length : 0;
  const maxScore    = allScores.length ? Math.max(...allScores) : 0;
  const minScore    = allScores.length ? Math.min(...allScores) : 0;
  const selected    = yearData[dept];
  const deptScore   = selected && selected.idf != null ? selected.idf : null;
  const prevDeptData= priorYearData[dept];
  const prevScore   = prevDeptData && prevDeptData.idf != null ? prevDeptData.idf : null;
  const variation   = deptScore !== null && prevScore !== null ? (deptScore - prevScore).toFixed(2) : '–';
  const gap         = (maxScore - minScore).toFixed(2);

  // Set all KPI elements (could be multiple per key if we had duplicates)
  document.querySelectorAll('[data-key="nationalAvg"]').forEach(el => el.textContent = nationalAvg.toFixed(2));
  document.querySelectorAll('[data-key="deptCount"]').forEach(el => el.textContent = allScores.length);
  document.querySelectorAll('[data-key="deptScore"]').forEach(el => el.textContent = deptScore !== null ? deptScore.toFixed(2) : 'N/A');
  document.querySelectorAll('[data-key="variation"]').forEach(el => {
    el.textContent = variation;
    el.classList.remove('positive','negative');
    if (variation !== '–') el.classList.add(parseFloat(variation) >= 0 ? 'positive' : 'negative');
  });
  document.querySelectorAll('[data-key="max"]').forEach(el => el.textContent = maxScore.toFixed(2));
  document.querySelectorAll('[data-key="min"]').forEach(el => el.textContent = minScore.toFixed(2));
  document.querySelectorAll('[data-key="gap"]').forEach(el => el.textContent = gap);

  // Dept name elements
  if (deptNameEl)       deptNameEl.textContent       = dept;
  if (histDeptNameEl)   histDeptNameEl.textContent    = dept;

  // Year labels
  ['top10Year','tipYear','catYear','distYear'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = `(${year})`;
  });

  // Map colors
  const svg = svgContainer.querySelector('svg');
  if (svg) {
    svg.querySelectorAll('path').forEach(p => {
      if (p.id === 'CO-DC') return;
      const score = getDeptScore(year, mapIdToDeptName(p.id));
      p.style.fill = score !== undefined ? getIdfColor(score) : '#d1d9e0';
    });
  }

  // Tables
  populateResultsTable(document.querySelector('#resultsTable tbody'),      selected, prevDeptData, true);
  populateManagementTable(document.querySelector('#managementTable tbody'), selected, prevDeptData, true);

  populateEvoTable(year);
  populateDistTable(year, priorYear);
  populateTop10Table(year);
  populateTipologiaTable(year);
  populateCategoriaTable(year);
  populateHistTable(dept);

  // Charts
  updateHistoricalChart(year, dept);
  updateNationalAvgChart(year);
  updateNationalDistChart(year);
  updateTop10Chart(year);
  updateTipologiaChart(year);
  updateCategoriaChart(year);
}

// ============================================================
//  DIMENSION TABLES
// ============================================================
function populateResultsTable(tbody, selected, prior, compact) {
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!selected || !selected.resultados || !selected.resultados.indicadores) return;
  const indicadores = selected.resultados.indicadores;
  const priorInd    = prior?.resultados?.indicadores || {};

  for (const [key, ind] of Object.entries(indicadores)) {
    const prev   = priorInd[key];
    const res    = ind.resultado;
    const cal    = ind.calificacion;
    const prevRes= prev ? prev.resultado   : null;
    const prevCal= prev ? prev.calificacion: null;
    const varRes = res != null && prevRes != null ? (res - prevRes).toFixed(2) : '–';
    const varCal = cal != null && prevCal != null ? (cal - prevCal).toFixed(2) : '–';
    const varCalNum = parseFloat(varCal);
    const varCalClass = !isNaN(varCalNum) ? (varCalNum > 0 ? 'cell-positive' : varCalNum < 0 ? 'cell-negative' : '') : '';

    const tr = document.createElement('tr');
    if (compact) {
      tr.innerHTML = `
        <td>${ind.nombre || key}</td>
        <td>${res != null ? res.toFixed(2) : '–'}</td>
        <td>${cal != null ? cal.toFixed(2) : '–'}</td>
        <td class="${varCalClass}">${varCal}</td>`;
    } else {
      tr.innerHTML = `
        <td>${ind.nombre || key}</td>
        <td>${res != null ? res.toFixed(2) : '–'}</td>
        <td>${cal != null ? cal.toFixed(2) : '–'}</td>
        <td>${prevRes != null ? prevRes.toFixed(2) : '–'}</td>
        <td>${prevCal != null ? prevCal.toFixed(2) : '–'}</td>
        <td>${varRes}</td>
        <td class="${varCalClass}">${varCal}</td>`;
    }
    tbody.appendChild(tr);
  }

  // Total row
  const totalRes  = selected.resultados.score;
  const totalCal  = selected.resultados.calificacion;
  const priorTRes = prior?.resultados?.score;
  const priorTCal = prior?.resultados?.calificacion;
  const trTotal   = document.createElement('tr');
  trTotal.className = 'total-row';
  const varTCal = totalCal != null && priorTCal != null ? (totalCal - priorTCal).toFixed(2) : '–';
  const varTCalNum  = parseFloat(varTCal);
  const varTCalClass= !isNaN(varTCalNum) ? (varTCalNum > 0 ? 'cell-positive' : varTCalNum < 0 ? 'cell-negative' : '') : '';

  if (compact) {
    trTotal.innerHTML = `
      <td>TOTAL RESULTADOS</td>
      <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
      <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
      <td class="${varTCalClass}">${varTCal}</td>`;
  } else {
    trTotal.innerHTML = `
      <td>TOTAL RESULTADOS</td>
      <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
      <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
      <td>${priorTRes != null ? priorTRes.toFixed(2) : '–'}</td>
      <td>${priorTCal != null ? priorTCal.toFixed(2) : '–'}</td>
      <td>${totalRes != null && priorTRes != null ? (totalRes - priorTRes).toFixed(2) : '–'}</td>
      <td class="${varTCalClass}">${varTCal}</td>`;
  }
  tbody.appendChild(trTotal);
}

function populateManagementTable(tbody, selected, prior, compact) {
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!selected || !selected.gestion || !selected.gestion.indicadores) return;
  const indicadores = selected.gestion.indicadores;
  const priorInd    = prior?.gestion?.indicadores || {};

  for (const [key, ind] of Object.entries(indicadores)) {
    const prev   = priorInd[key];
    const res    = ind.resultado;
    const cal    = ind.calificacion;
    const prevRes= prev ? prev.resultado   : null;
    const prevCal= prev ? prev.calificacion: null;
    const varRes = res != null && prevRes != null ? (res - prevRes).toFixed(2) : '–';
    const varCal = cal != null && prevCal != null ? (cal - prevCal).toFixed(2) : '–';
    const varCalNum = parseFloat(varCal);
    const varCalClass = !isNaN(varCalNum) ? (varCalNum > 0 ? 'cell-positive' : varCalNum < 0 ? 'cell-negative' : '') : '';

    const tr = document.createElement('tr');
    if (compact) {
      tr.innerHTML = `
        <td>${ind.nombre || key}</td>
        <td>${res != null ? res.toFixed(2) : '–'}</td>
        <td>${cal != null ? cal.toFixed(2) : '–'}</td>
        <td class="${varCalClass}">${varCal}</td>`;
    } else {
      tr.innerHTML = `
        <td>${ind.nombre || key}</td>
        <td>${res != null ? res.toFixed(2) : '–'}</td>
        <td>${cal != null ? cal.toFixed(2) : '–'}</td>
        <td>${prevRes != null ? prevRes.toFixed(2) : '–'}</td>
        <td>${prevCal != null ? prevCal.toFixed(2) : '–'}</td>
        <td>${varRes}</td>
        <td class="${varCalClass}">${varCal}</td>`;
    }
    tbody.appendChild(tr);
  }

  const totalRes  = selected.gestion.score;
  const totalCal  = selected.gestion.calificacion;
  const priorTRes = prior?.gestion?.score;
  const priorTCal = prior?.gestion?.calificacion;
  const trTotal   = document.createElement('tr');
  trTotal.className = 'total-row';
  const varTCal = totalCal != null && priorTCal != null ? (totalCal - priorTCal).toFixed(2) : '–';
  const varTCalNum  = parseFloat(varTCal);
  const varTCalClass= !isNaN(varTCalNum) ? (varTCalNum > 0 ? 'cell-positive' : varTCalNum < 0 ? 'cell-negative' : '') : '';

  if (compact) {
    trTotal.innerHTML = `
      <td>TOTAL GESTIÓN</td>
      <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
      <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
      <td class="${varTCalClass}">${varTCal}</td>`;
  } else {
    trTotal.innerHTML = `
      <td>TOTAL GESTIÓN</td>
      <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
      <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
      <td>${priorTRes != null ? priorTRes.toFixed(2) : '–'}</td>
      <td>${priorTCal != null ? priorTCal.toFixed(2) : '–'}</td>
      <td>${totalRes != null && priorTRes != null ? (totalRes - priorTRes).toFixed(2) : '–'}</td>
      <td class="${varTCalClass}">${varTCal}</td>`;
  }
  tbody.appendChild(trTotal);
}

// ============================================================
//  EVOLUTION TABLE
// ============================================================
function populateEvoTable(currentYear) {
  const tbody = document.querySelector('#evoTable tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  let prevAvg = null;
  idfData.years.forEach(y => {
    const yd     = idfData.byYear[y];
    const scores = Object.values(yd).map(d => d.idf).filter(v => v != null);
    const avg    = scores.length ? scores.reduce((a,b)=>a+b,0)/scores.length : 0;
    const max    = scores.length ? Math.max(...scores) : 0;
    const min    = scores.length ? Math.min(...scores) : 0;
    const varStr = prevAvg !== null ? (avg - prevAvg).toFixed(2) : '–';
    const varNum = parseFloat(varStr);
    const varClass = !isNaN(varNum) ? (varNum > 0 ? 'cell-positive' : varNum < 0 ? 'cell-negative' : '') : '';
    prevAvg = avg;
    const tr = document.createElement('tr');
    if (y === currentYear) tr.className = 'total-row';
    tr.innerHTML = `
      <td>${y}</td>
      <td>${avg.toFixed(2)}</td>
      <td class="${varClass}">${varStr}</td>
      <td>${scores.length}</td>
      <td>${max.toFixed(2)}</td>
      <td>${min.toFixed(2)}</td>`;
    tbody.appendChild(tr);
  });
}

// ============================================================
//  DISTRIBUTION TABLE (fills both distTable and distTable2)
// ============================================================
function populateDistTable(year, priorYear) {
  const yearData   = idfData.byYear[year];
  const allDepts   = Object.values(yearData);
  const total      = allDepts.length;
  const ranges     = ['Deterioro','Riesgo','Vulnerable','Solvente','Sostenible'];
  const rangeClss  = ['deterioro','riesgo','vulnerable','solvente','sostenible'];

  function fillTable(tbodyId, totalCantId, totalAvgId) {
    const tbody = document.querySelector(`#${tbodyId} tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    let totalCant = 0, totalWSum = 0;
    ranges.forEach((r, i) => {
      const deptScores = allDepts.filter(d => d.rango === r).map(d => d.idf).filter(v => v != null);
      const count = deptScores.length;
      const pct   = total > 0 ? ((count/total)*100).toFixed(1) : '0';
      const avg   = count > 0 ? (deptScores.reduce((a,b)=>a+b,0)/count).toFixed(2) : '–';
      totalCant += count;
      deptScores.forEach(s => totalWSum += s);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="rango-badge ${rangeClss[i]}">${r}</span></td>
        <td>${count}</td><td>${pct}%</td><td>${avg}</td>`;
      tbody.appendChild(tr);
    });
    const cantEl = document.getElementById(totalCantId);
    const avgEl  = document.getElementById(totalAvgId);
    if (cantEl) cantEl.textContent = totalCant;
    if (avgEl)  avgEl.textContent  = total > 0 ? (totalWSum/total).toFixed(2) : '–';
  }

  fillTable('distTable',  'distTotalCant',  'distTotalAvg');
  fillTable('distTable2', 'distTotalCant2', 'distTotalAvg2');
}

// ============================================================
//  TOP 10 TABLE
// ============================================================
function populateTop10Table(year) {
  const tbody = document.querySelector('#top10Table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const sorted   = Object.entries(yearData)
    .filter(([name]) => name !== 'BOGOTA D.C.')
    .sort((a,b) => (b[1].idf||0) - (a[1].idf||0))
    .slice(0,10);
  sorted.forEach(([name, obj], i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${i+1}</td>
      <td>${name}</td>
      <td>${obj.idf != null ? obj.idf.toFixed(2) : '–'}</td>
      <td><span class="rango-badge ${rangoBadgeClass(obj.rango)}">${getRangoLabel(obj.rango)}</span></td>`;
    tbody.appendChild(tr);
  });
}

// ============================================================
//  TIPOLOGÍA TABLE
// ============================================================
function populateTipologiaTable(year) {
  const tbody = document.querySelector('#tipologiaTable tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const yearData  = idfData.byYear[year];
  const depts     = Object.values(yearData);
  const tipMap    = {};
  depts.forEach(d => {
    const t = d.tipologia && d.tipologia !== 'N/A' ? d.tipologia : 'Sin tipología';
    if (!tipMap[t]) tipMap[t] = [];
    if (d.idf != null) tipMap[t].push(d);
  });
  const ranges = ['Deterioro','Riesgo','Vulnerable','Solvente','Sostenible'];
  let grandTotal = 0;
  for (const [tip, list] of Object.entries(tipMap)) {
    const tr = document.createElement('tr');
    let html = `<td>${tip}</td>`;
    let rowTotal = 0;
    ranges.forEach(r => { const c = list.filter(d=>d.rango===r).length; rowTotal+=c; html+=`<td>${c}</td>`; });
    grandTotal += rowTotal;
    html += `<td>${rowTotal}</td>`;
    tr.innerHTML = html;
    tbody.appendChild(tr);
  }
  if (Object.keys(tipMap).length > 1) {
    const trT = document.createElement('tr');
    trT.className = 'total-row';
    let html = '<td>TOTAL</td>';
    ranges.forEach(r => { html += `<td>${depts.filter(d=>d.rango===r).length}</td>`; });
    html += `<td>${grandTotal}</td>`;
    trT.innerHTML = html;
    tbody.appendChild(trT);
  }
}

// ============================================================
//  CATEGORÍA TABLE
// ============================================================
function populateCategoriaTable(year) {
  const tbody = document.querySelector('#categoriaTable tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const depts    = Object.values(yearData);
  const catMap   = { 'ESP':'Especial','1':'Primera','2':'Segunda','3':'Tercera','4':'Cuarta','N/A':'N/A' };
  const catBuckets = {};
  depts.forEach(d => {
    const cat = d.categoria && d.categoria !== 'N/A' ? d.categoria : 'N/A';
    if (!catBuckets[cat]) catBuckets[cat] = [];
    if (d.idf != null) catBuckets[cat].push(d);
  });
  const ranges   = ['Deterioro','Riesgo','Vulnerable','Solvente','Sostenible'];
  const catOrder = ['ESP','1','2','3','4','N/A'];
  let grandTotal = 0;
  catOrder.forEach(cat => {
    if (!catBuckets[cat]) return;
    const list = catBuckets[cat];
    const tr   = document.createElement('tr');
    let html   = `<td>${catMap[cat]||cat}</td>`;
    let rowTotal = 0;
    ranges.forEach(r => { const c=list.filter(d=>d.rango===r).length; rowTotal+=c; html+=`<td>${c}</td>`; });
    grandTotal += rowTotal;
    html += `<td>${rowTotal}</td>`;
    tr.innerHTML = html;
    tbody.appendChild(tr);
  });
  if (Object.keys(catBuckets).length > 1) {
    const trT = document.createElement('tr');
    trT.className = 'total-row';
    let html = '<td>TOTAL</td>';
    ranges.forEach(r => { html += `<td>${depts.filter(d=>d.rango===r).length}</td>`; });
    html += `<td>${grandTotal}</td>`;
    trT.innerHTML = html;
    tbody.appendChild(trT);
  }
}

// ============================================================
//  HISTORICAL DEPT TABLE
// ============================================================
function populateHistTable(dept) {
  const tbody = document.querySelector('#histTable tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  idfData.years.forEach(y => {
    const yd = idfData.byYear[y];
    if (!yd || !yd[dept]) return;
    const d  = yd[dept];
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${y}</td>
      <td>${d.region   || '–'}</td>
      <td>${d.categoria|| '–'}</td>
      <td>${d.tipologia|| '–'}</td>
      <td>${d.idf != null ? d.idf.toFixed(2) : '–'}</td>
      <td><span class="rango-badge ${rangoBadgeClass(d.rango)}">${getRangoLabel(d.rango)}</span></td>
      <td>${d.ranking  || '–'}</td>`;
    tbody.appendChild(tr);
  });
}

// ============================================================
//  CHARTS
// ============================================================
const CHART_BASE_OPTIONS = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(26,46,74,0.92)',
      titleFont: { family: 'Inter', size: 11, weight: 'bold' },
      bodyFont:  { family: 'Inter', size: 11 },
      padding: 8, cornerRadius: 6
    }
  }
};

// Historical line chart (Evolución section)
function updateHistoricalChart(currentYear, dept) {
  const years  = idfData.years;
  const scores = years.map(y => { const d = idfData.byYear[y]?.[dept]; return d ? d.idf : null; });
  const ctx    = document.getElementById('historicalChart');
  if (!ctx) return;

  if (historicalChart) {
    historicalChart.data.labels = years;
    historicalChart.data.datasets[0].data  = scores;
    historicalChart.data.datasets[0].label = `${dept} – IDF`;
    historicalChart.update();
    return;
  }
  historicalChart = new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: {
      labels: years,
      datasets: [{
        label: `${dept} – IDF`,
        data:  scores,
        borderColor: '#1d5fa8',
        backgroundColor: 'rgba(29,95,168,0.12)',
        tension: 0.35,
        pointRadius: 5,
        pointBackgroundColor: '#1d5fa8',
        fill: true,
        borderWidth: 2.5
      }]
    },
    options: {
      ...CHART_BASE_OPTIONS,
      plugins: { ...CHART_BASE_OPTIONS.plugins, legend: { display: true, labels: { font: { family:'Inter', size:11 }, color:'#4a5568' } } },
      scales: {
        y: { beginAtZero: false, min: 30, max: 100, grid: { color:'rgba(0,0,0,0.05)' }, ticks: { font:{family:'Inter',size:10} } },
        x: { grid: { display:false }, ticks: { font:{family:'Inter',size:10} } }
      }
    }
  });
}

// National average bar chart (shown in Evolución + Distribuciones)
function buildNationalAvgData() {
  return {
    labels: idfData.years,
    data:   idfData.years.map(y => {
      const s = Object.values(idfData.byYear[y]).map(d=>d.idf).filter(v=>v!=null);
      return s.length ? parseFloat((s.reduce((a,b)=>a+b,0)/s.length).toFixed(2)) : 0;
    })
  };
}

function updateNationalAvgChart(year) {
  const { labels, data } = buildNationalAvgData();
  const bgColors = labels.map(y => y === year ? '#1d5fa8' : 'rgba(29,95,168,0.45)');
  const ctx = document.getElementById('nationalAvgChart');
  if (!ctx) return;
  if (nationalAvgChart) {
    nationalAvgChart.data.labels = labels;
    nationalAvgChart.data.datasets[0].data = data;
    nationalAvgChart.data.datasets[0].backgroundColor = bgColors;
    nationalAvgChart.update();
    return;
  }
  nationalAvgChart = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels, datasets:[{ label:'IDF Prom. Nacional', data, backgroundColor: bgColors, borderRadius:4 }] },
    options: {
      ...CHART_BASE_OPTIONS,
      scales: {
        y: { beginAtZero: false, min:30, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{font:{family:'Inter',size:10}} },
        x: { grid:{display:false}, ticks:{font:{family:'Inter',size:10}} }
      }
    }
  });
}

// Donut for national distribution (Evolución section)
function updateNationalDistChart(year) {
  const yearData = idfData.byYear[year];
  const counts   = { Deterioro:0, Riesgo:0, Vulnerable:0, Solvente:0, Sostenible:0 };
  Object.values(yearData).forEach(d => {
    if (d.idf == null) return;
    const k = getIdfRangeKey(d.idf);
    counts[k.charAt(0).toUpperCase()+k.slice(1)]++;
  });
  const labels   = Object.keys(counts);
  const dataVals = Object.values(counts);
  const bgColors = [IDF_COLORS.deterioro, IDF_COLORS.riesgo, IDF_COLORS.vulnerable, IDF_COLORS.solvente, IDF_COLORS.sostenible];
  const ctx = document.getElementById('nationalDistributionChart');
  if (!ctx) return;
  if (nationalDistChart) {
    nationalDistChart.data.labels = labels;
    nationalDistChart.data.datasets[0].data = dataVals;
    nationalDistChart.update();
    return;
  }
  nationalDistChart = new Chart(ctx.getContext('2d'), {
    type: 'doughnut',
    data: { labels, datasets:[{ data: dataVals, backgroundColor: bgColors, borderWidth:1 }] },
    options: {
      ...CHART_BASE_OPTIONS,
      cutout: '55%',
      plugins: { ...CHART_BASE_OPTIONS.plugins, legend: { display: false } }
    }
  });
}

// Top 10 horizontal bar chart
function updateTop10Chart(year) {
  const yearData = idfData.byYear[year];
  const sorted   = Object.entries(yearData)
    .filter(([name]) => name !== 'BOGOTA D.C.')
    .sort((a,b) => (b[1].idf||0) - (a[1].idf||0))
    .slice(0,10);
  const labels = sorted.map(([name]) => name.length > 16 ? name.slice(0,15)+'…' : name);
  const scores = sorted.map(([,obj]) => obj.idf||0);
  const colors = sorted.map(([,obj]) => getIdfColor(obj.idf||0));
  const ctx    = document.getElementById('top10Chart');
  if (!ctx) return;
  if (top10Chart) {
    top10Chart.data.labels = labels;
    top10Chart.data.datasets[0].data = scores;
    top10Chart.data.datasets[0].backgroundColor = colors;
    top10Chart.update();
    return;
  }
  top10Chart = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels, datasets:[{ label:'IDF', data: scores, backgroundColor: colors, borderRadius:3 }] },
    options: {
      ...CHART_BASE_OPTIONS,
      indexAxis: 'y',
      scales: {
        x: { beginAtZero: true, max:100, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{font:{family:'Inter',size:9}} },
        y: { grid:{display:false}, ticks:{font:{family:'Inter',size:9}} }
      }
    }
  });
}

// Tipología grouped bar
function updateTipologiaChart(year) {
  const yearData = idfData.byYear[year];
  const depts    = Object.values(yearData);
  const tipMap   = {};
  depts.forEach(d => {
    const t = d.tipologia && d.tipologia !== 'N/A' ? d.tipologia : 'Sin tip.';
    if (!tipMap[t]) tipMap[t] = { Deterioro:0, Riesgo:0, Vulnerable:0, Solvente:0, Sostenible:0 };
    if (d.idf != null && d.rango) tipMap[t][d.rango] = (tipMap[t][d.rango]||0)+1;
  });
  const tipLabels = Object.keys(tipMap);
  const rangKeys  = ['Deterioro','Riesgo','Vulnerable','Solvente','Sostenible'];
  const bgList    = [IDF_COLORS.deterioro, IDF_COLORS.riesgo, IDF_COLORS.vulnerable, IDF_COLORS.solvente, IDF_COLORS.sostenible];
  const datasets  = rangKeys.map((r,i) => ({
    label: r,
    data:  tipLabels.map(t => tipMap[t][r]||0),
    backgroundColor: bgList[i],
    borderRadius: 3,
    barPercentage: 0.7
  }));
  const ctx = document.getElementById('tipologiaChart');
  if (!ctx) return;
  if (tipologiaChart) {
    tipologiaChart.data.labels   = tipLabels;
    tipologiaChart.data.datasets = datasets;
    tipologiaChart.update();
    return;
  }
  tipologiaChart = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels: tipLabels, datasets },
    options: {
      ...CHART_BASE_OPTIONS,
      plugins: {
        ...CHART_BASE_OPTIONS.plugins,
        legend: { display: true, labels:{ font:{family:'Inter',size:9}, padding:8 } }
      },
      scales: {
        y: { beginAtZero:true, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{font:{family:'Inter',size:9}, stepSize:1} },
        x: { grid:{display:false}, ticks:{font:{family:'Inter',size:9}} }
      }
    }
  });
}

// Categoría grouped bar
function updateCategoriaChart(year) {
  const yearData  = idfData.byYear[year];
  const depts     = Object.values(yearData);
  const catMap2   = { 'ESP':'Especial','1':'Primera','2':'Segunda','3':'Tercera','4':'Cuarta','N/A':'N/A' };
  const catBuckets2 = {};
  depts.forEach(d => {
    const cat = d.categoria && d.categoria !== 'N/A' ? d.categoria : 'N/A';
    const label = catMap2[cat] || cat;
    if (!catBuckets2[label]) catBuckets2[label] = { Deterioro:0, Riesgo:0, Vulnerable:0, Solvente:0, Sostenible:0 };
    if (d.idf != null && d.rango) catBuckets2[label][d.rango] = (catBuckets2[label][d.rango]||0)+1;
  });
  const catOrder2  = ['Especial','Primera','Segunda','Tercera','Cuarta','N/A'];
  const catLabels  = catOrder2.filter(l => catBuckets2[l]);
  const rangKeys   = ['Deterioro','Riesgo','Vulnerable','Solvente','Sostenible'];
  const bgList     = [IDF_COLORS.deterioro, IDF_COLORS.riesgo, IDF_COLORS.vulnerable, IDF_COLORS.solvente, IDF_COLORS.sostenible];
  const datasets   = rangKeys.map((r,i) => ({
    label: r,
    data:  catLabels.map(l => catBuckets2[l]?.[r]||0),
    backgroundColor: bgList[i],
    borderRadius: 3,
    barPercentage: 0.7
  }));
  const ctx = document.getElementById('categoriaChart');
  if (!ctx) return;
  if (categoriaChart) {
    categoriaChart.data.labels   = catLabels;
    categoriaChart.data.datasets = datasets;
    categoriaChart.update();
    return;
  }
  categoriaChart = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels: catLabels, datasets },
    options: {
      ...CHART_BASE_OPTIONS,
      plugins: {
        ...CHART_BASE_OPTIONS.plugins,
        legend: { display: true, labels:{ font:{family:'Inter',size:9}, padding:8 } }
      },
      scales: {
        y: { beginAtZero:true, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{font:{family:'Inter',size:9}, stepSize:1} },
        x: { grid:{display:false}, ticks:{font:{family:'Inter',size:9}} }
      }
    }
  });
}

// ============================================================
//  START
// ============================================================
init();
