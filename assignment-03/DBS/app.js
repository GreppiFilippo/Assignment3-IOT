/* ===== CONFIGURATION ===== */
const MAX_READINGS = 60;
const POLL_INTERVAL_MS = 2000;

// Chart visual constants
const CHART_POINT_RADIUS = 2;
const CHART_LINE_TENSION = 0.4;

const State = {
    MANUAL: "MANUAL",
    AUTOMATIC: "AUTOMATIC",
    UNCONNECTED: "UNCONNECTED",
    NOT_AVAILABLE: "NOT_AVAILABLE"
};

// API endpoints
const API_BASE = "http://localhost:8000/api/v1";
const ENDPOINT_READINGS = `${API_BASE}/levels`;
const ENDPOINT_STATUS = `${API_BASE}/status`;
const ENDPOINT_MODE = `${API_BASE}/mode`;
const ENDPOINT_VALVE = `${API_BASE}/valve`;

/* ===== STATE ===== */
let autoRefreshEnabled = true;
let refreshIntervalId = null;
let userInteractingWithSlider = false;

/* ===== DATA STORAGE ===== */
const labels = [];
const values = [];

/* ===== DOM ELEMENTS ===== */
const ctx = document.getElementById("levelChart");
const chartTitle = document.getElementById("chartTitle");
const sliderValue = document.getElementById("sliderValue");
const systemState = document.getElementById("systemState");
const valveOpening = document.getElementById("valveOpening");
const sendValveBtn = document.getElementById("sendValveBtn");
const switchModeBtn = document.getElementById("switchModeBtn");
const valveSlider = document.getElementById("valveSlider");
const toggleRefreshBtn = document.getElementById("toggleRefreshBtn");
const refreshIcon = document.getElementById("refreshIcon");
const lastUpdate = document.getElementById("lastUpdate");
const actionToast = document.getElementById("actionToast");
const toastTitle = document.getElementById("toastTitle");
const toastBody = document.getElementById("toastBody");
const toastIcon = document.getElementById("toastIcon");
const loadingOverlay = document.getElementById("loadingOverlay");

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

/**
 * Shows a toast notification to the user.
 * 
 * @param {string} title - Toast title
 * @param {string} message - Toast message body
 * @param {string} type - Toast type: 'success', 'error', 'info'
 */
function showToast(title, message, type = 'success') {
    toastTitle.textContent = title;
    toastBody.textContent = message;

    const toastHeader = actionToast.querySelector('.toast-header');
    toastHeader.className = 'toast-header';

    // Update icon based on type
    toastIcon.className = 'me-2';

    if (type === 'error') {
        toastHeader.classList.add('bg-danger', 'text-white');
        toastIcon.classList.add('bi', 'bi-exclamation-triangle-fill');
    } else if (type === 'success') {
        toastHeader.classList.add('bg-success', 'text-white');
        toastIcon.classList.add('bi', 'bi-check-circle-fill');
    } else {
        toastHeader.classList.add('bg-info', 'text-white');
        toastIcon.classList.add('bi', 'bi-info-circle-fill');
    }

    const toast = new bootstrap.Toast(actionToast);
    toast.show();
}

/**
 * Updates the "Last Updated" timestamp display.
 */
function updateLastUpdateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    lastUpdate.textContent = `Updated: ${timeString}`;
}

/* ===== CHART SETUP ===== */
const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Rainwater level (cm)",
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
                    text: 'Level (cm)'
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

        systemState.textContent = status.state ?? State.NOT_AVAILABLE;
        valveOpening.textContent = `${status.valve_opening ?? "--"}`;

        // Sync slider with current valve opening ONLY if user is not interacting
        if (!userInteractingWithSlider && status.valve_opening !== null && status.valve_opening !== undefined) {
            valveSlider.value = status.valve_opening;
            sliderValue.textContent = `${status.valve_opening}%`;
        }

        updateSystemStateBadge(status.state);
        updateManualControls(status.state);
        updateLastUpdateTimestamp();

    } catch (error) {
        console.error("Error fetching data:", error);
        systemState.textContent = State.NOT_AVAILABLE;
        valveOpening.textContent = "--";
        updateSystemStateBadge(State.NOT_AVAILABLE);
        updateManualControls(State.NOT_AVAILABLE);
        lastUpdate.textContent = "Update failed";
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
 * Updates ARIA attributes for accessibility.
 * 
 * @param {string} mode - Current system mode from State enum
 */
function updateManualControls(mode) {
    const isManual = (mode === State.MANUAL);
    valveSlider.disabled = !isManual;
    sendValveBtn.disabled = !isManual;
    valveSlider.setAttribute('aria-disabled', !isManual);
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
        showToast("Mode Changed", `Switched to ${newMode} mode`, 'success');
    } catch (error) {
        console.error("Error switching mode:", error);
        showToast("Error", "Failed to switch mode", 'error');
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
        showToast("Invalid Value", "Valve opening must be between 0-100%", 'error');
        return;
    }

    try {
        const response = await postJson(ENDPOINT_VALVE, { opening });
        if (!response.ok) throw new Error("Failed to set valve");

        showToast("Valve Updated", `Valve opening set to ${opening}%`, 'success');
    } catch (error) {
        console.error("Error setting valve:", error);
        showToast("Error", "Failed to set valve opening", 'error');
    }
}

/**
 * Toggles automatic data refresh on/off.
 */
function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;

    if (autoRefreshEnabled) {
        toggleRefreshBtn.className = "btn btn-success";
        toggleRefreshBtn.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
        startAutoRefresh();
    } else {
        toggleRefreshBtn.className = "btn btn-warning";
        toggleRefreshBtn.innerHTML = '<i class="bi bi-play-fill"></i> Resume';
        stopAutoRefresh();
    }
}

/**
 * Starts the automatic refresh interval.
 */
function startAutoRefresh() {
    if (refreshIntervalId) return;
    refreshIntervalId = setInterval(fetchLatest, POLL_INTERVAL_MS);
}

/**
 * Stops the automatic refresh interval.
 */
function stopAutoRefresh() {
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
        refreshIntervalId = null;
    }
}

/* ===== EVENT HANDLERS ===== */
valveSlider.addEventListener("mousedown", () => {
    userInteractingWithSlider = true;
});

valveSlider.addEventListener("mouseup", () => {
    userInteractingWithSlider = false;
});

valveSlider.addEventListener("touchstart", () => {
    userInteractingWithSlider = true;
});

valveSlider.addEventListener("touchend", () => {
    userInteractingWithSlider = false;
});

valveSlider.addEventListener("input", (event) => {
    const value = event.target.value;
    sliderValue.textContent = value + "%";
    valveSlider.setAttribute('aria-valuenow', value);
});

switchModeBtn.addEventListener("click", switchMode);
sendValveBtn.addEventListener("click", sendValve);
toggleRefreshBtn.addEventListener("click", toggleAutoRefresh);

/* ===== INITIALIZATION ===== */
// Update chart title with actual sample count
chartTitle.textContent = `Rainwater Level (last ${MAX_READINGS} samples)`;

// Initialize tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

// Show loading overlay on first load
loadingOverlay.classList.add('show');

startAutoRefresh();
fetchLatest().finally(() => {
    loadingOverlay.classList.remove('show');
});