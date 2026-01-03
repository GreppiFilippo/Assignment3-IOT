/* ===== CONFIGURATION ===== */
const MAX_READINGS = 60;
const POLL_INTERVAL_MS = 2000;

// Chart visual constants
const CHART_POINT_RADIUS = 2;
const CHART_LINE_TENSION = 0.4;
const CHART_ANIMATION_DURATION = 800;

const State = {
    MANUAL: "MANUAL",
    AUTOMATIC: "AUTOMATIC",
    UNCONNECTED: "UNCONNECTED",
    NOT_AVAILABLE: "NOT_AVAILABLE"
};

// API endpoints
const API_BASE = "http://localhost:8000/api";
const ENDPOINT_READINGS = `${API_BASE}/readings`;
const ENDPOINT_STATUS = `${API_BASE}/status`;
const ENDPOINT_MODE = `${API_BASE}/mode`;
const ENDPOINT_VALVE = `${API_BASE}/valve`;

/* ===== DATA STORAGE ===== */
const labels = [];
const values = [];

/* ===== DOM ELEMENTS ===== */
const ctx = document.getElementById("levelChart");
const sliderValue = document.getElementById("sliderValue");
const systemState = document.getElementById("systemState");
const valveOpening = document.getElementById("valveOpening");
const sendValveBtn = document.getElementById("sendValveBtn");
const switchModeBtn = document.getElementById("switchModeBtn");
const valveSlider = document.getElementById("valveSlider");

/* ===== HELPER FUNCTIONS ===== */
/**
 * Formats the tooltip title for chart hover interactions.
 * Converts timestamp to HH:MM:SS format.
 * 
 * @param {Array} items - Chart.js tooltip items array
 * @returns {string} Formatted time string (HH:MM:SS) or original label on error
 */
function formatTooltipTitle(items) {
    try {
        const value = items[0].parsed && items[0].parsed.x ? items[0].parsed.x : items[0].label;
        const date = new Date(value);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    } catch (error) {
        return items[0].label || '';
    }
}

/**
 * Helper function to perform POST requests with JSON payload.
 * 
 * @param {string} url - Target endpoint URL
 * @param {Object} data - Data object to be sent as JSON
 * @returns {Promise<Response>} Fetch response promise
 */
async function postJson(url, data) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
}

/* ===== CHART SETUP ===== */
const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Rainwater level (m)",
            data: values,
            backgroundColor: "rgba(54,162,235,0.2)",
            borderColor: "rgba(54,162,235,1)",
            pointRadius: CHART_POINT_RADIUS,
            fill: true,
            tension: CHART_LINE_TENSION
        }]
    },
    options: {
        responsive: true,
        animation: false,
        plugins: {
            tooltip: {
                callbacks: {
                    title: formatTooltipTitle
                }
            }
        },
        scales: {
            x: {
                type: "time",
                time: {
                    tooltipFormat: "HH:mm:ss"
                },
                display: false
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Level (m)'
                }
            }
        }
    }
});

/* ===== API FUNCTIONS ===== */
/**
 * Fetches latest sensor readings and system status from the backend.
 * Updates the chart with new data and refreshes UI elements (system state, valve opening).
 * Handles errors gracefully by displaying NOT_AVAILABLE state.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function fetchLatest() {
    try {
        const response = await fetch(`${ENDPOINT_READINGS}?limit=${MAX_READINGS}`);
        if (!response.ok) throw new Error(response.status);

        const data = await response.json();

        labels.length = 0;
        values.length = 0;

        data.forEach(reading => {
            labels.push(new Date(reading.ts));
            values.push(reading.value);
        });

        chart.update();

        const statusResponse = await fetch(ENDPOINT_STATUS);
        const status = await statusResponse.json();

        systemState.textContent = status.status ?? State.NOT_AVAILABLE;
        valveOpening.textContent = `${status.valve_opening ?? "--"}`;

        updateSystemStateBadge(status.mode);
        updateManualControls(status.mode);

    } catch (error) {
        console.error("Error fetching data:", error);
        systemState.textContent = State.NOT_AVAILABLE;
        valveOpening.textContent = "--";
        updateSystemStateBadge(State.NOT_AVAILABLE);
        updateManualControls(State.NOT_AVAILABLE);
    }
}

/**
 * Updates the visual appearance of the system state badge based on current mode.
 * Applies Bootstrap color classes: success (automatic), warning (manual), 
 * danger (unconnected), secondary (not available).
 * 
 * @param {string} mode - Current system mode from State enum
 */
function updateSystemStateBadge(mode) {
    systemState.className = "badge fs-6";

    switch (mode) {
        case State.AUTOMATIC:
            systemState.classList.add("bg-success");
            break;
        case State.MANUAL:
            systemState.classList.add("bg-warning");
            break;
        case State.UNCONNECTED:
            systemState.classList.add("bg-danger");
            break;
        default:
            systemState.classList.add("bg-secondary");
    }
}

/**
 * Enables or disables manual control UI elements based on system mode.
 * Manual controls (slider and button) are only active in MANUAL mode.
 * 
 * @param {string} mode - Current system mode from State enum
 */
function updateManualControls(mode) {
    const isManual = (mode === State.MANUAL);
    valveSlider.disabled = !isManual;
    sendValveBtn.disabled = !isManual;
}

/**
 * Toggles system mode between MANUAL and AUTOMATIC.
 * Fetches current status, determines opposite mode, sends update request,
 * and refreshes the UI on success.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function switchMode() {
    try {
        const statusResponse = await fetch(ENDPOINT_STATUS);
        if (!statusResponse.ok) throw new Error("No status");
        const status = await statusResponse.json();

        const newMode = (status.mode === State.MANUAL) ? State.AUTOMATIC : State.MANUAL;

        const response = await postJson(ENDPOINT_MODE, { mode: newMode });
        if (!response.ok) throw new Error("Failed to switch mode");

        await fetchLatest();
    } catch (error) {
        console.error("Error switching mode:", error);
        alert("Failed to switch mode");
    }
}

/**
 * Sends the current slider value as valve opening command to the backend.
 * Validates the value is within acceptable range (0-100) before sending.
 * Only functional when system is in MANUAL mode.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function sendValve() {
    const opening = parseInt(valveSlider.value);

    if (isNaN(opening) || opening < 0 || opening > 100) {
        console.error("Invalid valve opening value:", opening);
        return;
    }

    try {
        const response = await postJson(ENDPOINT_VALVE, { opening });
        if (!response.ok) throw new Error("Failed to set valve");

    } catch (error) {
        console.error("Error setting valve:", error);
        alert("Failed to set valve opening");
    }
}

/* ===== EVENT HANDLERS ===== */
valveSlider.addEventListener("input", (event) => {
    sliderValue.textContent = event.target.value + "%";
});

switchModeBtn.addEventListener("click", switchMode);
sendValveBtn.addEventListener("click", sendValve);

/* ===== INITIALIZATION ===== */
setInterval(fetchLatest, POLL_INTERVAL_MS);
fetchLatest();