// === Configuration ===
const DATA_URL = './datos_idf.json';
const SVG_URL = 'colombia_dep.svg';

let idfData = null;
let currentZoom = 1;
let panX = 0;
let panY = 0;
let isPanning = false;
let panStart = {x: 0, y: 0};
let selectedDeptPath = null;

const yearSelect = document.getElementById('yearSelect');
const deptSelect = document.getElementById('deptSelect');
const svgContainer = document.getElementById('svgMapContainer');
const deptNameEl = document.getElementById('deptName');
const histDeptNameEl = document.getElementById('histDeptName');

const IDF_COLORS = {
  deterioro: '#ff7f7f',
  riesgo: '#ffb84d',
  vulnerable: '#ffea7f',
  solvente: '#95e080',
  sostenible: '#28a745'
};
const IDF_RANGES = [
  { key: 'deterioro', label: 'Deterioro (<40)', min: 0, max: 40 },
  { key: 'riesgo', label: 'Riesgo (40‑<60)', min: 40, max: 60 },
  { key: 'vulnerable', label: 'Vulnerable (60‑<70)', min: 60, max: 70 },
  { key: 'solvente', label: 'Solvente (70‑<80)', min: 70, max: 80 },
  { key: 'sostenible', label: 'Sostenible (≥80)', min: 80, max: 101 }
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
function getRangoLabel(rango) {
  const map = {
    'Deterioro': '1. Deterioro (<40)',
    'Riesgo': '2. Riesgo (≥40 y <60)',
    'Vulnerable': '3. Vulnerable (≥60 y <70)',
    'Solvente': '4. Solvente (≥70 y <80)',
    'Sostenible': '5. Sostenible (≥80)',
    'N/A': 'N/A'
  };
  return map[rango] || rango || 'N/A';
}
function rangoBadgeClass(rango) {
  const map = {
    'Deterioro': 'deterioro', 'Riesgo': 'riesgo', 'Vulnerable': 'vulnerable',
    'Solvente': 'solvente', 'Sostenible': 'sostenible'
  };
  return map[rango] || 'riesgo';
}

const kpiElements = {
  nationalAvg: document.querySelector('[data-key="nationalAvg"]'),
  deptCount: document.querySelector('[data-key="deptCount"]'),
  deptScore: document.querySelector('[data-key="deptScore"]'),
  variation: document.querySelector('[data-key="variation"]'),
  max: document.querySelector('[data-key="max"]'),
  min: document.querySelector('[data-key="min"]'),
  gap: document.querySelector('[data-key="gap"]')
};

const resultsTableBody = document.querySelector('#resultsTable tbody');
const managementTableBody = document.querySelector('#managementTable tbody');
const evoTableBody = document.querySelector('#evoTable tbody');
const distTableBody = document.querySelector('#distTable tbody');
const top10TableBody = document.querySelector('#top10Table tbody');
const tipologiaTableBody = document.querySelector('#tipologiaTable tbody');
const categoriaTableBody = document.querySelector('#categoriaTable tbody');
const histTableBody = document.querySelector('#histTable tbody');

let historicalChart = null;
let nationalDistChart = null;
let top10Chart = null;

// SVG-id → UPPERCASE department name (matches JSON keys)
const idToDept = {
  'CO-AMA': 'AMAZONAS', 'CO-ANT': 'ANTIOQUIA', 'CO-ARA': 'ARAUCA',
  'CO-ATL': 'ATLANTICO', 'CO-BOL': 'BOLIVAR', 'CO-BOY': 'BOYACA',
  'CO-CAL': 'CALDAS', 'CO-CAQ': 'CAQUETA', 'CO-CAS': 'CASANARE',
  'CO-CAU': 'CAUCA', 'CO-CES': 'CESAR', 'CO-CHO': 'CHOCO',
  'CO-COR': 'CORDOBA', 'CO-CUN': 'CUNDINAMARCA', 'CO-DC': 'BOGOTA D.C.',
  'CO-GUA': 'GUAINIA', 'CO-GUV': 'GUAVIARE', 'CO-HUI': 'HUILA',
  'CO-LAG': 'GUAJIRA', 'CO-MAG': 'MAGDALENA', 'CO-MET': 'META',
  'CO-NAR': 'NARIÑO', 'CO-NSA': 'NORTE DE SANTANDER', 'CO-PUT': 'PUTUMAYO',
  'CO-QUI': 'QUINDIO', 'CO-RIS': 'RISARALDA', 'CO-SAN': 'SANTANDER',
  'CO-SAP': 'SAN ANDRÉS', 'CO-SUC': 'SUCRE', 'CO-TOL': 'TOLIMA',
  'CO-VAC': 'VALLE DEL CAUCA', 'CO-VAU': 'VAUPES', 'CO-VID': 'VICHADA'
};

function mapIdToDeptName(id) {
  if (idToDept[id]) return idToDept[id];
  return id.replace('CO-', '').replace(/_/g, ' ').toUpperCase();
}

function getDeptScore(year, deptName) {
  const yearData = idfData.byYear[year];
  if (!yearData) return undefined;
  const d = yearData[deptName];
  return d ? d.idf : undefined;
}

// ---- INIT ----
async function init() {
  try {
    const [dataResp, svgResp] = await Promise.all([
      fetch(DATA_URL).catch(e => { console.error('JSON fetch failed:', e); throw e; }),
      fetch(SVG_URL).catch(e => { console.error('SVG fetch failed:', e); throw e; })
    ]);
    if (!dataResp.ok) throw new Error('JSON ' + dataResp.status);
    if (!svgResp.ok) throw new Error('SVG ' + svgResp.status);
    const rawData = await dataResp.json();
    idfData = { years: rawData.meta.anios, departments: rawData.meta.departamentos, byYear: rawData.records };
    const svgText = await svgResp.text();
    injectSvg(svgText);
    populateYearSelector();
    populateDeptSelector();
    attachEventHandlers();
    setupZoomControls();
    setupPanControls();
    updateDashboard(yearSelect.value, deptSelect.value);
  } catch (err) {
    console.error('Init error:', err);
    const msg = document.createElement('div');
    msg.style.cssText = 'position:fixed;top:10px;right:10px;background:#ffdddd;color:#900;padding:12px;border:1px solid #900;border-radius:6px;z-index:9999;font-size:0.9rem;';
    msg.textContent = 'Error al cargar datos. Use un servidor HTTP.';
    document.body.appendChild(msg);
  }
}

// ---- SVG MAP ----
function injectSvg(svgContent) {
  svgContainer.innerHTML = svgContent;
  const svg = svgContainer.querySelector('svg');
  if (!svg) return;
  // Set explicit dimensions based on the SVG's native size
  svg.removeAttribute('width');
  svg.removeAttribute('height');
  svg.setAttribute('viewBox', '0 0 612.82 693.68');
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.style.width = '100%';
  svg.style.height = '100%';
  svg.style.maxWidth = '100%';
  svg.style.maxHeight = '100%';
  svg.id = 'colombiaSvg';
  svg.querySelectorAll('path').forEach(path => {
    const deptId = path.id;
    if (deptId === 'CO-DC') {
      path.addEventListener('mouseenter', () => showTooltip(path, 'Bogotá D.C. (No aplica)'));
      path.addEventListener('mouseleave', hideTooltip);
      return;
    }
    const deptName = mapIdToDeptName(deptId);
    path.addEventListener('mouseenter', () => {
      const score = getDeptScore(yearSelect.value, deptName);
      showTooltip(path, `${deptName}\nIDF: ${score !== undefined ? score.toFixed(2) : 'N/A'}`);
    });
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
  const targetId = Object.entries(idToDept).find(([, v]) => v === deptName);
  if (targetId) {
    const el = svg.getElementById(targetId[0]);
    if (el) el.classList.add('selected-dept');
  }
}

// ---- ZOOM ----
function setupZoomControls() {
  document.getElementById('zoomIn').addEventListener('click', () => {
    currentZoom = Math.min(5, currentZoom * 1.3);
    applyZoom();
  });
  document.getElementById('zoomOut').addEventListener('click', () => {
    currentZoom = Math.max(0.3, currentZoom / 1.3);
    applyZoom();
  });
  document.getElementById('zoomReset').addEventListener('click', () => {
    currentZoom = 1;
    applyZoom();
  });
}
function applyZoom() {
  const svg = svgContainer.querySelector('svg');
  if (!svg) return;
  svg.style.transform = `translate(${panX}px, ${panY}px) scale(${currentZoom})`;
  svg.style.transformOrigin = '0 0';
}

// ============ Pan controls ============
function setupPanControls() {
  const container = svgContainer;
  container.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    isPanning = true;
    panStart.x = e.clientX;
    panStart.y = e.clientY;
    document.body.style.cursor = 'grabbing';
    e.preventDefault();
  });
  document.addEventListener('mousemove', (e) => {
    if (!isPanning) return;
    const dx = e.clientX - panStart.x;
    const dy = e.clientY - panStart.y;
    panX += dx;
    panY += dy;
    panStart.x = e.clientX;
    panStart.y = e.clientY;
    applyZoom();
  });
  document.addEventListener('mouseup', () => {
    if (isPanning) {
      isPanning = false;
      document.body.style.cursor = 'default';
    }
  });
  container.addEventListener('mouseleave', () => {
    if (isPanning) {
      isPanning = false;
      document.body.style.cursor = 'default';
    }
  });
}

// ---- TOOLTIP ----
let tooltipDiv = null;
function createTooltipDiv() {
  tooltipDiv = document.createElement('div');
  tooltipDiv.style.cssText = 'position:absolute;padding:6px 10px;background:rgba(0,0,0,0.82);color:#fff;border-radius:4px;pointer-events:none;font-size:0.82rem;z-index:1000;white-space:pre-line;';
  document.body.appendChild(tooltipDiv);
}
function showTooltip(target, text) {
  if (!tooltipDiv) createTooltipDiv();
  tooltipDiv.textContent = text;
  const rect = target.getBoundingClientRect();
  tooltipDiv.style.left = `${rect.right + 5}px`;
  tooltipDiv.style.top = `${rect.top}px`;
  tooltipDiv.style.display = 'block';
}
function hideTooltip() { if (tooltipDiv) tooltipDiv.style.display = 'none'; }

// ---- POPULATE SELECTORS ----
function populateYearSelector() {
  idfData.years.forEach(y => {
    const opt = document.createElement('option');
    opt.value = y; opt.textContent = y;
    yearSelect.appendChild(opt);
  });
  yearSelect.value = idfData.years[idfData.years.length - 1];
}
function populateDeptSelector() {
  idfData.departments.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d; opt.textContent = d;
    deptSelect.appendChild(opt);
  });
  deptSelect.value = idfData.departments[0];
}
function attachEventHandlers() {
  yearSelect.addEventListener('change', () => updateDashboard(yearSelect.value, deptSelect.value));
  deptSelect.addEventListener('change', () => updateDashboard(yearSelect.value, deptSelect.value));
}

// ---- MAIN UPDATE ----
function updateDashboard(year, dept) {
  if (!idfData) return;
  const yearData = idfData.byYear[year];
  if (!yearData) return;
  const priorYear = (parseInt(year) - 1).toString();
  const priorYearData = idfData.byYear[priorYear] || {};

  // Highlight selected dept on map
  highlightDeptOnMap(dept);

  // ---- KPIs ----
  const allScores = Object.values(yearData).map(d => d.idf).filter(v => v != null);
  const priorAllScores = Object.values(priorYearData).map(d => d.idf).filter(v => v != null);
  const nationalAvg = allScores.length ? allScores.reduce((a, b) => a + b, 0) / allScores.length : 0;
  const maxScore = allScores.length ? Math.max(...allScores) : 0;
  const minScore = allScores.length ? Math.min(...allScores) : 0;
  const selected = yearData[dept];
  const deptScore = selected && selected.idf != null ? selected.idf : null;
  const prevDeptData = priorYearData[dept];
  const prevScore = prevDeptData && prevDeptData.idf != null ? prevDeptData.idf : null;
  const priorAvg = priorAllScores.length ? priorAllScores.reduce((a, b) => a + b, 0) / priorAllScores.length : 0;
  const variation = (deptScore !== null && prevScore !== null) ? (deptScore - prevScore).toFixed(2) : '–';
  const gap = (maxScore - minScore).toFixed(2);

  kpiElements.nationalAvg.textContent = nationalAvg.toFixed(2);
  kpiElements.deptCount.textContent = allScores.length;
  kpiElements.deptScore.textContent = deptScore !== null ? deptScore.toFixed(2) : 'N/A';
  kpiElements.variation.textContent = variation;
  kpiElements.max.textContent = maxScore.toFixed(2);
  kpiElements.min.textContent = minScore.toFixed(2);
  kpiElements.gap.textContent = gap;

  deptNameEl.textContent = dept;
  histDeptNameEl.textContent = dept;

  // ---- Map colors ----
  const svg = svgContainer.querySelector('svg');
  if (svg) {
    svg.querySelectorAll('path').forEach(p => {
      if (p.id === 'CO-DC') return;
      const dName = mapIdToDeptName(p.id);
      const score = getDeptScore(year, dName);
      p.style.fill = score !== undefined ? getIdfColor(score) : '#e0e0e0';
    });
  }

  // ---- Dimension tables ----
  populateResultsTable(resultsTableBody, selected, prevDeptData);
  populateManagementTable(managementTableBody, selected, prevDeptData);

  // ---- Evolution table ----
  populateEvoTable(year);

  // ---- Distribution table ----
  populateDistTable(year, priorYear);

  // ---- Top 10 ----
  populateTop10Table(year);
  updateTop10Chart(year);

  // ---- Tipología ----
  populateTipologiaTable(year);

  // ---- Categoría Ley 617 ----
  populateCategoriaTable(year);

  // ---- Historical dept query ----
  populateHistTable(dept);

  // ---- Charts ----
  updateHistoricalChart(year, dept);
  updateNationalDistChart(year);
}

// ---- DIMENSION TABLES ----
function populateResultsTable(tbody, selected, prior) {
  tbody.innerHTML = '';
  if (!selected || !selected.resultados || !selected.resultados.indicadores) return;
  const indicadores = selected.resultados.indicadores;
  const priorInd = prior && prior.resultados && prior.resultados.indicadores ? prior.resultados.indicadores : {};
  for (const [key, ind] of Object.entries(indicadores)) {
    const prev = priorInd[key];
    const res = ind.resultado;
    const cal = ind.calificacion;
    const prevRes = prev ? prev.resultado : null;
    const prevCal = prev ? prev.calificacion : null;
    const varRes = (res != null && prevRes != null) ? (res - prevRes).toFixed(2) : '–';
    const varCal = (cal != null && prevCal != null) ? (cal - prevCal).toFixed(2) : '–';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${ind.nombre || key}</td>
      <td>${res != null ? res.toFixed(2) : '–'}</td>
      <td>${cal != null ? cal.toFixed(2) : '–'}</td>
      <td>${prevRes != null ? prevRes.toFixed(2) : '–'}</td>
      <td>${prevCal != null ? prevCal.toFixed(2) : '–'}</td>
      <td>${varRes}</td>
      <td>${varCal}</td>`;
    tbody.appendChild(tr);
  }
  // Total row
  const totalRes = selected.resultados.score;
  const totalCal = selected.resultados.calificacion;
  const priorTotalRes = prior && prior.resultados ? prior.resultados.score : null;
  const priorTotalCal = prior && prior.resultados ? prior.resultados.calificacion : null;
  const trTotal = document.createElement('tr');
  trTotal.style.fontWeight = '700';
  trTotal.innerHTML = `
    <td>TOTAL RESULTADOS</td>
    <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
    <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
    <td>${priorTotalRes != null ? priorTotalRes.toFixed(2) : '–'}</td>
    <td>${priorTotalCal != null ? priorTotalCal.toFixed(2) : '–'}</td>
    <td>${totalRes != null && priorTotalRes != null ? (totalRes - priorTotalRes).toFixed(2) : '–'}</td>
    <td>${totalCal != null && priorTotalCal != null ? (totalCal - priorTotalCal).toFixed(2) : '–'}</td>`;
  tbody.appendChild(trTotal);
}

function populateManagementTable(tbody, selected, prior) {
  tbody.innerHTML = '';
  if (!selected || !selected.gestion || !selected.gestion.indicadores) return;
  const indicadores = selected.gestion.indicadores;
  const priorInd = prior && prior.gestion && prior.gestion.indicadores ? prior.gestion.indicadores : {};
  for (const [key, ind] of Object.entries(indicadores)) {
    const prev = priorInd[key];
    const res = ind.resultado;
    const cal = ind.calificacion;
    const prevRes = prev ? prev.resultado : null;
    const prevCal = prev ? prev.calificacion : null;
    const varRes = (res != null && prevRes != null) ? (res - prevRes).toFixed(2) : '–';
    const varCal = (cal != null && prevCal != null) ? (cal - prevCal).toFixed(2) : '–';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${ind.nombre || key}</td>
      <td>${res != null ? res.toFixed(2) : '–'}</td>
      <td>${cal != null ? cal.toFixed(2) : '–'}</td>
      <td>${prevRes != null ? prevRes.toFixed(2) : '–'}</td>
      <td>${prevCal != null ? prevCal.toFixed(2) : '–'}</td>
      <td>${varRes}</td>
      <td>${varCal}</td>`;
    tbody.appendChild(tr);
  }
  const totalRes = selected.gestion.score;
  const totalCal = selected.gestion.calificacion;
  const priorTotalRes = prior && prior.gestion ? prior.gestion.score : null;
  const priorTotalCal = prior && prior.gestion ? prior.gestion.calificacion : null;
  const trTotal = document.createElement('tr');
  trTotal.style.fontWeight = '700';
  trTotal.innerHTML = `
    <td>TOTAL GESTIÓN</td>
    <td>${totalRes != null ? totalRes.toFixed(2) : '–'}</td>
    <td>${totalCal != null ? totalCal.toFixed(2) : '–'}</td>
    <td>${priorTotalRes != null ? priorTotalRes.toFixed(2) : '–'}</td>
    <td>${priorTotalCal != null ? priorTotalCal.toFixed(2) : '–'}</td>
    <td>${totalRes != null && priorTotalRes != null ? (totalRes - priorTotalRes).toFixed(2) : '–'}</td>
    <td>${totalCal != null && priorTotalCal != null ? (totalCal - priorTotalCal).toFixed(2) : '–'}</td>`;
  tbody.appendChild(trTotal);
}

// ---- EVOLUTION TABLE ----
function populateEvoTable(currentYear) {
  evoTableBody.innerHTML = '';
  let prevAvg = null;
  idfData.years.forEach(y => {
    const yd = idfData.byYear[y];
    const scores = Object.values(yd).map(d => d.idf).filter(v => v != null);
    const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    const max = scores.length ? Math.max(...scores) : 0;
    const min = scores.length ? Math.min(...scores) : 0;
    const variation = prevAvg !== null ? (avg - prevAvg).toFixed(2) : '–';
    prevAvg = avg;
    const tr = document.createElement('tr');
    if (y === currentYear) tr.style.fontWeight = '700';
    tr.innerHTML = `<td>${y}</td><td>${avg.toFixed(2)}</td><td>${variation}</td><td>${scores.length}</td><td>${max.toFixed(2)}</td><td>${min.toFixed(2)}</td>`;
    evoTableBody.appendChild(tr);
  });
}

// ---- DISTRIBUTION TABLE ----
function populateDistTable(year, priorYear) {
  distTableBody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const priorData = idfData.byYear[priorYear] || {};
  const allDepts = Object.values(yearData);
  const priorDepts = Object.values(priorData);
  const total = allDepts.length;

  const ranges = ['Deterioro', 'Riesgo', 'Vulnerable', 'Solvente', 'Sostenible'];
  const rangeClasses = ['deterioro', 'riesgo', 'vulnerable', 'solvente', 'sostenible'];
  let totalCant = 0;
  let totalWeightedSum = 0;

  ranges.forEach((r, i) => {
    const count = allDepts.filter(d => d.rango === r).length;
    const priorCount = priorDepts.filter(d => d.rango === r).length;
    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
    const deptScores = allDepts.filter(d => d.rango === r).map(d => d.idf).filter(v => v != null);
    const avg = deptScores.length ? (deptScores.reduce((a, b) => a + b, 0) / deptScores.length).toFixed(2) : '–';
    totalCant += count;
    deptScores.forEach(s => totalWeightedSum += s);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="rango-badge ${rangeClasses[i]}">${r}</span></td>
      <td>${count}</td>
      <td>${pct}%</td>
      <td>${avg}</td>`;
    distTableBody.appendChild(tr);
  });

  document.getElementById('distTotalCant').textContent = totalCant;
  document.getElementById('distTotalAvg').textContent = total > 0 ? (totalWeightedSum / total).toFixed(2) : '–';
}

// ---- TOP 10 TABLE ----
function populateTop10Table(year) {
  top10TableBody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const sorted = Object.entries(yearData)
    .filter(([name]) => name !== 'BOGOTA D.C.')
    .sort((a, b) => (b[1].idf || 0) - (a[1].idf || 0))
    .slice(0, 10);
  sorted.forEach(([name, obj], i) => {
    const tr = document.createElement('tr');
    const badge = rangoBadgeClass(obj.rango);
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${name}</td>
      <td>${obj.idf != null ? obj.idf.toFixed(2) : '–'}</td>
      <td><span class="rango-badge ${badge}">${getRangoLabel(obj.rango)}</span></td>`;
    top10TableBody.appendChild(tr);
  });
}

// ---- TIPOLOGÍA TABLE ----
function populateTipologiaTable(year) {
  tipologiaTableBody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const depts = Object.values(yearData);
  const tipologias = {};
  depts.forEach(d => {
    const t = d.tipologia && d.tipologia !== 'N/A' ? d.tipologia : 'Sin tipología';
    if (!tipologias[t]) tipologias[t] = [];
    if (d.idf != null) tipologias[t].push(d);
  });
  const ranges = ['Deterioro', 'Riesgo', 'Vulnerable', 'Solvente', 'Sostenible'];
  let grandTotal = 0;
  for (const [tip, deptList] of Object.entries(tipologias)) {
    const tr = document.createElement('tr');
    let rowHtml = `<td>${tip}</td>`;
    let rowTotal = 0;
    ranges.forEach(r => {
      const count = deptList.filter(d => d.rango === r).length;
      rowTotal += count;
      rowHtml += `<td>${count}</td>`;
    });
    grandTotal += rowTotal;
    const scores = deptList.map(d => d.idf).filter(v => v != null);
    const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : '–';
    rowHtml += `<td>${rowTotal}</td><td>${avg}</td>`;
    tr.innerHTML = rowHtml;
    tipologiaTableBody.appendChild(tr);
  }
  // Total row
  if (Object.keys(tipologias).length > 1) {
    const trTotal = document.createElement('tr');
    trTotal.style.fontWeight = '700';
    let totalHtml = '<td>TOTAL</td>';
    ranges.forEach(r => {
      const count = depts.filter(d => d.rango === r).length;
      totalHtml += `<td>${count}</td>`;
    });
    const allScores = depts.map(d => d.idf).filter(v => v != null);
    const avgAll = allScores.length ? (allScores.reduce((a, b) => a + b, 0) / allScores.length).toFixed(2) : '–';
    totalHtml += `<td>${grandTotal}</td><td>${avgAll}</td>`;
    trTotal.innerHTML = totalHtml;
    tipologiaTableBody.appendChild(trTotal);
  }
}

// ---- CATEGORÍA LEY 617 TABLE ----
function populateCategoriaTable(year) {
  categoriaTableBody.innerHTML = '';
  const yearData = idfData.byYear[year];
  const depts = Object.values(yearData);
  const catMap = { 'ESP': 'Especial', '1': 'Primera', '2': 'Segunda', '3': 'Tercera', '4': 'Cuarta' };
  const categorias = {};
  depts.forEach(d => {
    const cat = d.categoria && d.categoria !== 'N/A' ? d.categoria : 'N/A';
    if (!categorias[cat]) categorias[cat] = [];
    if (d.idf != null) categorias[cat].push(d);
  });
  const ranges = ['Deterioro', 'Riesgo', 'Vulnerable', 'Solvente', 'Sostenible'];
  const rangeClasses = ['deterioro', 'riesgo', 'vulnerable', 'solvente', 'sostenible'];
  let grandTotal = 0;
  const catOrder = ['ESP', '1', '2', '3', '4', 'N/A'];
  catOrder.forEach(cat => {
    if (!categorias[cat]) return;
    const deptList = categorias[cat];
    const tr = document.createElement('tr');
    let rowHtml = `<td>${catMap[cat] || cat}</td>`;
    let rowTotal = 0;
    ranges.forEach((r, ri) => {
      const count = deptList.filter(d => d.rango === r).length;
      rowTotal += count;
      rowHtml += `<td>${count}</td>`;
    });
    grandTotal += rowTotal;
    const scores = deptList.map(d => d.idf).filter(v => v != null);
    const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : '–';
    rowHtml += `<td>${rowTotal}</td><td>${avg}</td>`;
    tr.innerHTML = rowHtml;
    categoriaTableBody.appendChild(tr);
  });
  // Total row
  if (Object.keys(categorias).length > 1) {
    const trTotal = document.createElement('tr');
    trTotal.style.fontWeight = '700';
    let totalHtml = '<td>TOTAL</td>';
    ranges.forEach(r => {
      const count = depts.filter(d => d.rango === r).length;
      totalHtml += `<td>${count}</td>`;
    });
    const allScores = depts.map(d => d.idf).filter(v => v != null);
    const avgAll = allScores.length ? (allScores.reduce((a, b) => a + b, 0) / allScores.length).toFixed(2) : '–';
    totalHtml += `<td>${grandTotal}</td><td>${avgAll}</td>`;
    trTotal.innerHTML = totalHtml;
    categoriaTableBody.appendChild(trTotal);
  }
}

// ---- HISTORICAL DEPT TABLE ----
function populateHistTable(dept) {
  histTableBody.innerHTML = '';
  idfData.years.forEach(y => {
    const yd = idfData.byYear[y];
    if (!yd || !yd[dept]) return;
    const d = yd[dept];
    const tr = document.createElement('tr');
    const badge = rangoBadgeClass(d.rango);
    tr.innerHTML = `
      <td>${y}</td>
      <td>${d.region || '–'}</td>
      <td>${d.categoria || '–'}</td>
      <td>${d.tipologia || '–'}</td>
      <td>${d.idf != null ? d.idf.toFixed(2) : '–'}</td>
      <td><span class="rango-badge ${badge}">${getRangoLabel(d.rango)}</span></td>
      <td>${d.ranking || '–'}</td>`;
    histTableBody.appendChild(tr);
  });
}

// ---- CHARTS ----
function updateHistoricalChart(currentYear, dept) {
  const years = idfData.years;
  const scores = years.map(y => {
    const d = idfData.byYear[y] && idfData.byYear[y][dept];
    return d ? d.idf : null;
  });
  const ctx = document.getElementById('historicalChart').getContext('2d');
  if (historicalChart) {
    historicalChart.data.labels = years;
    historicalChart.data.datasets[0].data = scores;
    historicalChart.data.datasets[0].label = `${dept} – IDF`;
    historicalChart.update();
    return;
  }
  historicalChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: years,
      datasets: [{ label: `${dept} – IDF`, data: scores, borderColor: '#0f4c81', backgroundColor: 'rgba(15,76,129,0.2)', tension: 0.3, pointRadius: 4, fill: true }]
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } }
  });
}

function updateNationalDistChart(year) {
  const yearData = idfData.byYear[year];
  const ranges = { Deterioro: 0, Riesgo: 0, Vulnerable: 0, Solvente: 0, Sostenible: 0 };
  Object.values(yearData).forEach(d => {
    if (d.idf == null) return;
    const k = getIdfRangeKey(d.idf);
    const label = k.charAt(0).toUpperCase() + k.slice(1);
    ranges[label]++;
  });
  const ctx = document.getElementById('nationalDistributionChart').getContext('2d');
  const dataVals = Object.values(ranges);
  const labels = Object.keys(ranges);
  const bgColors = [IDF_COLORS.deterioro, IDF_COLORS.riesgo, IDF_COLORS.vulnerable, IDF_COLORS.solvente, IDF_COLORS.sostenible];
  if (nationalDistChart) {
    nationalDistChart.data.labels = labels;
    nationalDistChart.data.datasets[0].data = dataVals;
    nationalDistChart.update();
    return;
  }
  nationalDistChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Deptos.', data: dataVals, backgroundColor: bgColors }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
  });
}

function updateTop10Chart(year) {
  const yearData = idfData.byYear[year];
  const sorted = Object.entries(yearData)
    .filter(([name]) => name !== 'BOGOTA D.C.')
    .sort((a, b) => (b[1].idf || 0) - (a[1].idf || 0))
    .slice(0, 10);
  const labels = sorted.map(([name]) => name);
  const scores = sorted.map(([, obj]) => obj.idf || 0);
  const ctx = document.getElementById('top10Chart').getContext('2d');
  if (top10Chart) {
    top10Chart.data.labels = labels;
    top10Chart.data.datasets[0].data = scores;
    top10Chart.update();
    return;
  }
  top10Chart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Top 10 IDF', data: scores, backgroundColor: '#28a745' }] },
    options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, max: 100 } } }
  });
}

init();
