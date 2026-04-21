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
const sections = document.querySelectorAll('.bento-section');

let simulationTemplates = [];
let selectedTemplate = null;

// Scroll Management
// Native anchor scrolling is used with Intersection Observer for active nav highlighting.

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
    
    const isDecisionMode = !document.getElementById('decision-mode-content').classList.contains('hidden');
    let payload;

    if (isDecisionMode) {
        const scenario = document.querySelector('.decision-card.selected').dataset.scenario;
        payload = getScenarioPayload(scenario);
    } else {
        payload = {
            densities: document.getElementById('densities').value,
            dimension_scales: document.getElementById('dimension_scales').value,
            regions: String(document.getElementById('regions').value),
            scenarios: String(document.getElementById('scenarios').value),
            time_units: String(document.getElementById('time_units').value),
            num_nodes: String(document.getElementById('num_nodes').value),
            initial_shock: String(document.getElementById('initial_shock').value)
        };
    }

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
            updateStats(data, payload);
            populateTable(data);
            generateAnalystReport(data, payload);
            
            resultsTableTile.classList.remove('hidden');
            breakPointAnnotation.classList.remove('hidden'); 
            
            // Auto-scroll to Outcome Analyst if in Decision Mode
            if (isDecisionMode) {
                setTimeout(() => {
                    const outcomeSection = document.getElementById('outcome-section');
                    outcomeSection.scrollIntoView({ behavior: 'smooth' });
                }, 1000);
            }
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
 * Returns N discrete colors from a standard high-contrast palette
 */
function getStandardPalette(n) {
    const standardColors = [
        '#2563EB', // Blue
        '#DC2626', // Red
        '#10B981', // Emerald
        '#F59E0B', // Amber/Orange
        '#7C3AED', // Purple
        '#0891B2', // Cyan
        '#EA580C', // Orange
        '#4F46E5', // Indigo
        '#BE185D'  // Pink
    ];
    
    const palette = [];
    for (let i = 0; i < n; i++) {
        palette.push(standardColors[i % standardColors.length]);
    }
    return palette;
}

function updateStats(data, payload) {
    const dimensionScalesStr = payload.dimension_scales;
    const scales = String(dimensionScalesStr).split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (data.datasets.length === 0) return;

    const lastDataset = data.datasets[data.datasets.length - 1];
    const validData = lastDataset.data.filter(v => v !== null && v !== 0);
    
    // Cascade Cost: Mean impact of the highest scale
    const avgImpact = validData.reduce((a, b) => a + b, 0) / validData.length;
    statLatency.innerText = Math.round(avgImpact || 0).toLocaleString();
    
    // Dynamic Break Point: Where highest scale crosses 5x initial shock
    const shockThreshold = Number(payload.initial_shock) * 5;
    let bpIndex = lastDataset.data.findIndex(v => v > shockThreshold);
    if (bpIndex === -1) bpIndex = data.labels.length - 1;
    statBreak.innerText = data.labels[bpIndex] || "Safe";
    
    // Cascade Factor: Max / Start ratio
    const startVal = lastDataset.data[0] || 1;
    const factor = Math.max(...validData) / startVal;
    statCascade.innerText = factor.toFixed(2);
    
    // Total Nodes in biggest scale
    statNodes.innerText = payload.num_nodes ? Number(payload.num_nodes).toLocaleString() : "—";
}

function getScenarioPayload(scenario) {
    const scenarios = {
        'isolated': {
            densities: "0.05, 0.1, 0.15, 0.2, 0.25",
            dimension_scales: "10, 20, 30, 50",
            regions: "5", scenarios: "10", time_units: "12", num_nodes: "500", initial_shock: "100000"
        },
        'regional': {
            densities: "0.2, 0.4, 0.6, 0.8, 1.0",
            dimension_scales: "20, 50, 80, 100",
            regions: "15", scenarios: "15", time_units: "24", num_nodes: "1000", initial_shock: "500000"
        },
        'systemic': {
            densities: "0.5, 0.8, 1.0, 1.2, 1.5",
            dimension_scales: "50, 100, 200, 500",
            regions: "40", scenarios: "20", time_units: "48", num_nodes: "2000", initial_shock: "1000000"
        },
        'black_swan': {
            densities: "1.0, 2.0, 3.0, 5.0, 10.0",
            dimension_scales: "100, 250, 500, 1000",
            regions: "100", scenarios: "50", time_units: "72", num_nodes: "5000", initial_shock: "5000000"
        }
    };
    return scenarios[scenario];
}

function generateAnalystReport(data, payload) {
    try {
        if (!data || !data.datasets || data.datasets.length === 0) return;

        const lastDataset = data.datasets[data.datasets.length - 1];
        const validData = lastDataset.data.filter(v => v !== null && v !== 0);
        if (validData.length === 0) return;

        const shockThreshold = Number(payload.initial_shock) * 5;
        const startVal = lastDataset.data[0] || 1;
        const maxVal = Math.max(...validData);
        const factor = maxVal / startVal;
        
        let bpIndex = lastDataset.data.findIndex(v => v > shockThreshold);
        const hasBroken = bpIndex !== -1;
        const bpDensity = hasBroken ? data.labels[bpIndex] : null;

        // Dedicated Tab Elements
        const outcomeSummary = document.getElementById('outcome-summary');
        const outcomeAction = document.getElementById('outcome-action');
        const outcomeChip = document.getElementById('outcome-chip');
        const exLatency = document.getElementById('ex-latency-val');
        const exBreak = document.getElementById('ex-break-val');
        const exFactor = document.getElementById('ex-factor-val');
        const trendDesc = document.getElementById('visual-trend-desc');

        if (exLatency) exLatency.innerText = `${Math.round(maxVal).toLocaleString()}`;
        if (exBreak) exBreak.innerText = hasBroken ? bpDensity : "Safe";
        if (exFactor) exFactor.innerText = `${factor.toFixed(2)}x`;

        // --- Intelligence Logic Matrix ---
        let summaryText = "";
        let actionText = "";
        let chipText = "STABLE SYSTEM";
        let chipColor = "#10B981";

        const isHighFactor = factor > 5;
        const isCriticalLatency = maxVal > 1000000;
        const isEarlyBreak = hasBroken && parseFloat(bpDensity) < 1.0;
        
        // Scenario A: Black Swan / Total Collapse
        if (hasBroken && isHighFactor && isCriticalLatency) {
            summaryText = `Warning: Systemic total fracture detected. The network hit a terminal "Feedback Loop" at ${bpDensity} density. Risk didn't just spread; it mutated, resulting in a ${factor.toFixed(1)}x amplification that renders structural recovery impossible.`;
            actionText = "Full system reset required. Physical decoupling of regional nodes is the only way to contain the bleed. Current scale is working against you.";
            chipText = "CRITICAL COLLAPSE";
            chipColor = "#EF4444";
        } 
        // Scenario B: Volatile Fragility (Low break point, high factor)
        else if (isEarlyBreak && isHighFactor) {
            summaryText = `This network is deceptively fragile. It snaps early (at ${bpDensity}) but the resulting explosion is massive. This suggests "Hyper-Dependency"—where even minor regions hold too much systemic weight.`;
            actionText = "Decentralize core region roles. Your Cascade Factor of ${factor.toFixed(1)}x suggests your network is built like a 'house of cards'—efficient but zero-tolerance for error.";
            chipText = "VOLATILE FRAGILITY";
            chipColor = "#F97316";
        }
        // Scenario C: Delayed Stress (Late break, high latency)
        else if (hasBroken && !isEarlyBreak) {
            summaryText = `The system is robust but has a "hard ceiling." It handles moderate stress perfectly until density hits ${bpDensity}, at which point it suffers a "Shear Failure." It's strong until it isn't.`;
            actionText = "Implement safety valves for high-density operations. Your break point is late, which often leads to complacency. Pre-emptively de-leverage when density hits 0.8.";
            chipText = "LATE-STAGE FRACTURE";
            chipColor = "#F59E0B";
        }
        // Scenario D: Stable with friction (No break, moderate factor)
        else if (!hasBroken && factor > 2) {
            summaryText = `Systemic friction is present. While the network hasn't broken, the ${factor.toFixed(1)}x multiplier indicates that shocks are reverberating across scales. The system is "Elastic"—it bends but hasn't snapped yet.`;
            actionText = "Monitor the 'Cascade Cost.' Even without a break point, the cost of dealing with internal stress is rising. Scale back nodes to reduce internal noise.";
            chipText = "FRAGILE ELASTICITY";
            chipColor = "#EAB308";
        }
        // Scenario E: Robust Efficiency
        else {
            summaryText = `The structural architecture is optimal. Shocks are localized and absorbed. The current density allows for "Risk Insulation," where failures in one region fail to reach the systemic core.`;
            actionText = "Safe to scale. You have significant headroom before hitting any density thresholds. Maintain current connectivity patterns.";
            chipText = "ROBUST ARCHITECTURE";
            chipColor = "#10B981";
        }

        // --- Visual Intelligence ---
        if (trendDesc) {
            if (hasBroken && isHighFactor) {
                trendDesc.innerText = "The vertical 'Exponential Spike' signifies a loss of system control. The geometry of the risk is no longer linear; it is a self-sustaining contagion.";
            } else if (factor > 3) {
                trendDesc.innerText = "The 'Parabolic Curve' shows risk accelerating faster than the density increases. This is a classic indicator of systemic friction before a potential break.";
            } else {
                trendDesc.innerText = "The 'Linear Trajectory' suggests the system is absorbing shock at a constant rate. This is the desired behavior for a resilient infrastructure.";
            }
        }

        // Sync Dedicated Tab
        if (outcomeSummary) outcomeSummary.innerText = summaryText;
        if (outcomeAction) outcomeAction.innerText = actionText;
        if (outcomeChip) {
            outcomeChip.innerText = chipText;
            outcomeChip.style.background = chipColor;
            outcomeChip.style.color = "#FFF";
        }
    } catch (err) {
        console.error("Analyst Report Failure:", err);
    }
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

    const colors = getStandardPalette(data.datasets.length);

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

// --- Event Analyzer Logic ---

async function loadTemplates() {
    try {
        const response = await fetch('template.json');
        const data = await response.json();
        simulationTemplates = data.simulations;
        renderTemplateDropdown();
    } catch (err) {
        console.error("Failed to load templates:", err);
    }
}

function renderTemplateDropdown() {
    const list = document.getElementById('template-dropdown-list');
    const btn = document.getElementById('template-dropdown-btn');
    
    list.innerHTML = simulationTemplates.map((sim, index) => `
        <div class="template-option" data-index="${index}">
            ${sim.event}
        </div>
    `).join('');

    // Toggle Dropdown
    btn.onclick = (e) => {
        e.stopPropagation();
        const isOpen = btn.classList.toggle('open');
        list.classList.toggle('open');
        
        // Ensure the parent tile has high z-index when open to avoid clipping by next section
        const parentTile = btn.closest('.tile');
        if (parentTile) {
            parentTile.style.zIndex = isOpen ? "1000" : "1";
        }
    };

    // Close on click outside
    document.addEventListener('click', () => {
        btn.classList.remove('open');
        list.classList.remove('open');
        const parentTile = btn.closest('.tile');
        if (parentTile) parentTile.style.zIndex = "1";
    });

    // Select Template
    list.querySelectorAll('.template-option').forEach(option => {
        option.onclick = () => {
            const index = option.dataset.index;
            selectTemplate(simulationTemplates[index]);
            btn.querySelector('span').innerText = simulationTemplates[index].event;
        };
    });
}

function selectTemplate(template) {
    selectedTemplate = template;
    
    // Show details
    const details = document.getElementById('selected-template-details');
    details.classList.remove('hidden');
    document.getElementById('template-event-name').innerText = template.event;
    document.getElementById('template-event-desc').innerText = 
        `Historical mapping: ${template.stress_parameters.scale} scale event with ${template.stress_parameters.propagation_type} propagation.`;

    // Update Translation Grid (Helping users understand the mapping)
    document.getElementById('rw-complexity').innerText = `Complexity: ${template.stress_parameters.propagation_type.replace('_', ' ')}`;
    document.getElementById('mi-density').innerText = `Density: ${template.stress_parameters.density}`;
    
    document.getElementById('rw-scope').innerText = `Horizon: ${template.stress_parameters.time_horizon.replace('_', ' ')}`;
    document.getElementById('mi-regions').innerText = `Scale Points: ${template.risk_cube_dimensions.regions.length}`;
    
    document.getElementById('rw-severity').innerText = `Impact: ${(template.stress_parameters.shock_magnitude * 100).toFixed(0)}% Intensity`;
    document.getElementById('mi-shock').innerText = `Shock: ${(1000000 * template.stress_parameters.shock_magnitude).toLocaleString()}`;

    // Update Risk Cube Lists
    renderList('assets-list', template.risk_cube_dimensions.assets);
    renderList('regions-list', template.risk_cube_dimensions.regions);
    renderList('scenarios-list', template.risk_cube_dimensions.scenarios);
}

function renderList(id, items) {
    const el = document.getElementById(id);
    el.innerHTML = items.map(item => `<li>${item.replace(/_/g, ' ')}</li>`).join('');
}

// Apply Template & Run
document.getElementById('apply-template-btn').onclick = () => {
    if (!selectedTemplate) return;

    // 1. Populate main form
    const p = selectedTemplate.stress_parameters;
    const d = selectedTemplate.risk_cube_dimensions;

    // Model specific translation:
    // We map the single density to a range for the chart visualization
    const densityVal = p.density;
    document.getElementById('densities').value = `${(densityVal * 0.5).toFixed(1)}, ${(densityVal * 0.8).toFixed(1)}, ${densityVal.toFixed(1)}, ${(densityVal * 1.2).toFixed(1)}, ${(densityVal * 1.5).toFixed(1)}`;
    
    document.getElementById('dimension_scales').value = "10, 50, 100, 250"; // Keep standard scales for comparison
    document.getElementById('regions').value = d.regions.length * 5; // Scale up regions for model
    document.getElementById('scenarios').value = d.scenarios.length * 5;
    document.getElementById('initial_shock').value = 1000000 * p.shock_magnitude;
    document.getElementById('time_units').value = parseInt(p.time_horizon.split('_')[0].substring(2)) || 12;
    document.getElementById('num_nodes').value = 1000; // Standard high fidelity for templates

    // 2. Switch to simulation tab
    navLinks[0].click();

    // 3. Trigger submit
    form.requestSubmit();
};

// --- Mode Switching & Decision Logic ---
document.getElementById('toggle-expert').onclick = () => {
    document.getElementById('simulation-form').classList.remove('hidden');
    document.getElementById('decision-mode-content').classList.add('hidden');
    document.getElementById('toggle-expert').classList.add('active');
    document.getElementById('toggle-decision').classList.remove('active');
};

document.getElementById('toggle-decision').onclick = () => {
    document.getElementById('simulation-form').classList.add('hidden');
    document.getElementById('decision-mode-content').classList.remove('hidden');
    document.getElementById('toggle-expert').classList.remove('active');
    document.getElementById('toggle-decision').classList.add('active');
};

document.querySelectorAll('.decision-card').forEach(card => {
    card.onclick = () => {
        document.querySelectorAll('.decision-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        // Sync Decision Mode with Expert Mode Inputs
        const scenarioData = getScenarioPayload(card.dataset.scenario);
        if (scenarioData) {
            document.getElementById('densities').value = scenarioData.densities;
            document.getElementById('dimension_scales').value = scenarioData.dimension_scales;
            document.getElementById('regions').value = scenarioData.regions;
            document.getElementById('scenarios').value = scenarioData.scenarios;
            document.getElementById('initial_shock').value = scenarioData.initial_shock;
            document.getElementById('time_units').value = scenarioData.time_units;
            document.getElementById('num_nodes').value = scenarioData.num_nodes;
        }
    };
});

document.getElementById('decision-run-btn').onclick = () => {
    form.requestSubmit();
};

// --- Scroll-Position Dependent Animations ---
function initScrollAnimations() {
    const tiles = document.querySelectorAll('.tile');
    const sections = document.querySelectorAll('.bento-section');
    const navLinks = document.querySelectorAll('.nav-link');

    function updateAnimations() {
        const vh = window.innerHeight;
        const threshold = vh * 0.3; // Slightly wider for even smoother transition
        
        tiles.forEach(tile => {
            const rect = tile.getBoundingClientRect();
            let progress = 1;

            if (rect.top > vh - threshold) {
                const dist = rect.top - (vh - threshold);
                progress = Math.max(0, 1 - (dist / threshold));
            } 
            else if (rect.bottom < threshold) {
                const dist = threshold - rect.bottom;
                progress = Math.max(0, 1 - (dist / threshold));
            }

            // Buttery Smooth 'Smoothstep' Easing (3x^2 - 2x^3)
            const easedProgress = progress * progress * (3 - 2 * progress);

            // Apply transformations with softer intensities
            tile.style.opacity = Math.max(0.15, easedProgress);
            tile.style.filter = `blur(${(1 - easedProgress) * 8}px)`;
            tile.style.transform = `translateY(${(1 - easedProgress) * 20}px) scale(${0.98 + (easedProgress * 0.02)})`;
        });

        // Navigation Tracking
        let current = "";
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (window.pageYOffset >= (sectionTop - 300)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });

        requestAnimationFrame(updateAnimations);
    }

    // Start loop
    requestAnimationFrame(updateAnimations);
}

// Initial State
window.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    loadTemplates(); 
});
