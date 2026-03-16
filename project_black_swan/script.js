// Minimalist 'Bento Refined' Scripting
Chart.defaults.color = '#71717A'; 
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 10;
Chart.defaults.font.weight = 600;

let performanceChart = null;

const form = document.getElementById('simulation-form');
const btn = document.getElementById('run-btn');
const statusDot = document.getElementById('system-status-dot');
const statusText = document.getElementById('system-status-text');
const canvas = document.getElementById('resultsChart');
const emptyState = document.getElementById('empty-state');
const emptyStateText = document.getElementById('empty-state-text');
const chartLoader = document.getElementById('chart-loader');
const breakPointAnnotation = document.getElementById('break-point-annotation');

// Debounce helper
function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

// Metrics elements
const statLatency = document.getElementById('stat-latency');
const statBreak = document.getElementById('stat-break');
const statCascade = document.getElementById('stat-cascade');
const statNodes = document.getElementById('stat-nodes');

// Table elements
const resultsTableTile = document.getElementById('results-table-tile');
const tableHead = document.getElementById('table-head-row');
const tableBody = document.getElementById('table-body');

// Navigation
const navLinks = document.querySelectorAll('.nav-link');

// Slider Value Labels
const sliderInputs = document.querySelectorAll('.slider');
const valueLabels = {
    'densities': document.getElementById('label-densities'),
    'dimension_scales': document.getElementById('label-dimension_scales'),
    'regions': document.getElementById('label-regions'),
    'scenarios': document.getElementById('label-scenarios'),
    'initial_shock': document.getElementById('label-initial_shock')
};

// Initialize listeners
const debouncedSubmit = debounce(() => form.dispatchEvent(new Event('submit')), 350);

sliderInputs.forEach(input => {
    input.addEventListener('input', () => {
        let val = input.value;
        if (input.id === 'initial_shock') {
            val = (val / 1000000).toFixed(1) + 'M';
        }
        if (valueLabels[input.id]) {
            valueLabels[input.id].innerText = val;
        }
    });
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI State
    btn.disabled = true;
    btn.style.opacity = "0.5";
    statusDot.style.background = "#F59E0B"; 
    if (statusText) statusText.innerText = "CALCULATING";
    
    canvas.style.display = 'none';
    emptyState.style.display = 'flex';
    emptyStateText.innerText = "CALCULATING FRACTURE DATA...";
    chartLoader.classList.remove('hidden');
    resultsTableTile.classList.add('hidden');
    
    // Generate Density Range for curve visualization
    const maxDensity = parseFloat(document.getElementById('densities').value);
    const densitySteps = 8;
    const densityArray = Array.from({length: densitySteps}, (_, i) => {
        const val = 0.1 + (i * (maxDensity - 0.1) / (densitySteps - 1));
        return val.toFixed(2);
    }).join(',');

    // Generate Scale comparative lines
    const maxScale = parseInt(document.getElementById('dimension_scales').value);
    const scalesArray = [Math.round(maxScale * 0.5), maxScale].join(',');

    const payload = {
        densities: densityArray,
        dimension_scales: scalesArray,
        regions: String(document.getElementById('regions').value),
        scenarios: String(document.getElementById('scenarios').value),
        time_units: String(document.getElementById('time_units').value),
        num_nodes: String(document.getElementById('num_nodes').value),
        initial_shock: String(document.getElementById('initial_shock').value)
    };

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const data = await response.json();
        
        if (data.error) {
            alert(`Simulation Error: ${data.error}`);
        } else {
            renderChart(data);
            updateStats(data, payload.dimension_scales);
            populateTable(data);
            resultsTableTile.classList.remove('hidden');
            breakPointAnnotation.classList.remove('hidden'); 
        }
    } catch (err) {
        console.error("Link Failure", err);
    } finally {
        btn.disabled = false;
        btn.style.opacity = "1";
        chartLoader.classList.add('hidden');
        emptyStateText.innerText = "Set your stress parameters. Run the test. Find the break point.";
        statusDot.style.background = "#10B981"; 
        if (statusText) statusText.innerText = "STANDBY";
    }
});

/**
 * Returns N discrete colors from a luxury Blue -> Green -> Red gradient
 */
function getGradientPalette(n) {
    const colors = [
        [37, 99, 235],   // Institutional Blue (#2563EB)
        [16, 185, 129],  // Emerald Green (#10B981)
        [220, 38, 38]    // Crimson Red (#DC2626)
    ];

    if (n <= 1) return [`rgb(${colors[0].join(',')})`];
    
    const palette = [];
    for (let i = 0; i < n; i++) {
        const t = i / (n - 1);
        let r, g, b;

        if (t <= 0.5) {
            // Blue to Green
            const f = t * 2;
            r = Math.round(colors[0][0] + f * (colors[1][0] - colors[0][0]));
            g = Math.round(colors[0][1] + f * (colors[1][1] - colors[0][1]));
            b = Math.round(colors[0][2] + f * (colors[1][2] - colors[0][2]));
        } else {
            // Green to Red
            const f = (t - 0.5) * 2;
            r = Math.round(colors[1][0] + f * (colors[2][0] - colors[1][0]));
            g = Math.round(colors[1][1] + f * (colors[2][1] - colors[1][1]));
            b = Math.round(colors[1][2] + f * (colors[2][2] - colors[1][2]));
        }
        palette.push(`rgb(${r},${g},${b})`);
    }
    return palette;
}

function updateStats(data, dimensionScalesStr) {
    const scales = String(dimensionScalesStr).split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (data.datasets.length === 0) return;

    const lastDataset = data.datasets[data.datasets.length - 1];
    const validData = lastDataset.data.filter(v => v !== null && v !== 0);
    
    // Cascade Cost: Mean latency of the highest scale
    const avgLatency = validData.reduce((a, b) => a + b, 0) / validData.length;
    statLatency.innerText = Math.round(avgLatency || 0).toLocaleString();
    
    // Dynamic Break Point: Where highest scale crosses 500k µs
    let bpIndex = lastDataset.data.findIndex(v => v > 500000);
    if (bpIndex === -1) bpIndex = data.labels.length - 1;
    statBreak.innerText = data.labels[bpIndex] || "Safe";
    
    // Cascade Factor: Max / Start ratio
    const startVal = lastDataset.data[0] || 1;
    const factor = Math.max(...validData) / startVal;
    statCascade.innerText = factor.toFixed(2);
    
    // Total Nodes in biggest scale
    statNodes.innerText = Number(document.getElementById('num_nodes').value).toLocaleString();
}

function populateTable(data) {
    // Headers
    tableHead.innerHTML = '<th>Step (Density)</th>' + 
        data.datasets.map(ds => `<th>Scale: ${ds.label}</th>`).join('');

    // Rows
    tableBody.innerHTML = '';
    data.labels.forEach((label, i) => {
        const row = document.createElement('tr');
        let rowHtml = `<td>${label}</td>`;
        data.datasets.forEach(ds => {
            const val = ds.data[i];
            rowHtml += `<td>${val ? Math.round(val).toLocaleString() : '—'}</td>`;
        });
        row.innerHTML = rowHtml;
        tableBody.appendChild(row);
    });
}

function renderChart(data) {
    emptyState.style.display = 'none';
    chartLoader.classList.add('hidden'); // Ensure loader is hidden when chart shows
    canvas.style.display = 'block';

    if (performanceChart) performanceChart.destroy();

    const colors = getGradientPalette(data.datasets.length);

    const datasets = data.datasets.map((ds, index) => {
        const color = colors[index];
        return {
            label: ds.label,
            data: ds.data.map(y => y === 0 ? null : y),
            borderColor: color,
            borderWidth: 2.0, // Thinned out for analytical density (prev 4.5)
            pointRadius: 0,
            pointHoverRadius: 5, // Balanced hover feel
            pointBackgroundColor: color,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            tension: 0, 
            fill: false
        };
    });

    performanceChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.labels.map(l => String(l)),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    backgroundColor: '#18181B',
                    titleColor: '#FFF',
                    cornerRadius: 6,
                    padding: 12
                },
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 8,
                        usePointStyle: true,
                        font: { weight: '700', size: 10 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { weight: 700 } }
                },
                y: {
                    type: 'logarithmic',
                    grid: { color: '#F1F5F9' },
                    ticks: { font: { weight: 700 } },
                    border: { display: false }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    });
}

// Simple Nav Intersection Highlight
window.addEventListener('scroll', () => {
    let current = "";
    const sections = document.querySelectorAll('.bento-section');
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= sectionTop - 120) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active');
        }
    });
});
