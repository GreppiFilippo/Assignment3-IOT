const N = 60;
const pollIntervalMs = 2000;
const labels = [];
const values = [];

// API endpoints
const API_BASE = "http://localhost:8000/api";

const ENDPOINT_READINGS = `${API_BASE}/readings`;
const ENDPOINT_STATUS = `${API_BASE}/status`;
const ENDPOINT_MODE = `${API_BASE}/mode`;
const ENDPOINT_VALVE = `${API_BASE}/valve`;

const State = {
    MANUAL: "MANUAL",
    AUTOMATIC: "AUTOMATIC",
    UNCONNECTED: "UNCONNECTED",
    NOT_AVAILABLE: "NOT_AVAILABLE"
};

/* Doc Elements */
const ctx = document.getElementById("levelChart");
const sliderValue = document.getElementById("sliderValue");
const systemState = document.getElementById("systemState");
const valveOpening = document.getElementById("valveOpening");
const sendValveBtn = document.getElementById("sendValveBtn");
const switchModeBtn = document.getElementById("switchModeBtn");
const valveSlider = document.getElementById("valveSlider");

const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "Rainwater level (m)",
            data: values,
            backgroundColor: "rgba(54,162,235,0.2)",
            borderColor: "rgba(54,162,235,1)",
            pointRadius: 2,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        animation: {
            duration: 800,
            easing: "easeOutCubic"
        },
        plugins: {
            tooltip: {
                callbacks: {
                    title: function (items) {
                        try {
                            const v = items[0].parsed && items[0].parsed.x ? items[0].parsed.x : items[0].label;
                            const d = new Date(v);
                            const hh = String(d.getHours()).padStart(2, '0');
                            const mm = String(d.getMinutes()).padStart(2, '0');
                            const ss = String(d.getSeconds()).padStart(2, '0');
                            return `${hh}:${mm}:${ss}`;
                        } catch (e) {
                            return items[0].label || '';
                        }
                    }
                }
            }
        },
        scales: {
            x: {
                type: "time",
                time: {
                    tooltipFormat: "HH:mm:ss",
                    unit: 'minute',
                    displayFormats: {
                        second: "HH:mm:ss",
                        minute: "HH:mm",
                        hour: "HH:mm"
                    }
                },
                ticks: {
                    display: false,
                    autoSkip: true,
                    maxTicksLimit: 8
                }
            },
            y: {
                beginAtZero: true
            }
        }
    }
});

async function fetchLatest() {
    try {
        const res = await fetch(`${ENDPOINT_READINGS}?limit=${N}`);
        if (!res.ok) throw new Error(res.status);

        const data = await res.json();

        labels.length = 0;
        values.length = 0;

        data.forEach(p => {
            labels.push(new Date(p.ts));
            values.push(p.value);
        });

        chart.update();

        const statusRes = await fetch(ENDPOINT_STATUS);
        const st = await statusRes.json();

        systemState.textContent = st.status ?? State.NOT_AVAILABLE;

        // API returns `valve_opening` according to schemas
        valveOpening.textContent = `${st.valve_opening ?? "--"}`;

        updateSystemStateBadge(st.mode);
        updateManualControls(st.mode);

    } catch {
        systemState.textContent = State.NOT_AVAILABLE;
        valveOpening.textContent = "--";
        updateSystemStateBadge(State.NOT_AVAILABLE);
        updateManualControls(State.NOT_AVAILABLE);
    }
}

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

function updateManualControls(mode) {
    const isManual = (mode === State.MANUAL);
    valveSlider.disabled = !isManual;
    sendValveBtn.disabled = !isManual;
}

async function switchMode() {
    try {
        // read current status to determine target mode
        const statusRes = await fetch(ENDPOINT_STATUS);
        if (!statusRes.ok) throw new Error("No status");
        const st = await statusRes.json();

        const newMode = (st.mode === State.MANUAL) ? State.AUTOMATIC : State.MANUAL;

        const payload = JSON.stringify({ mode: newMode });
        const res = await fetch(ENDPOINT_MODE, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload
        });

        if (!res.ok) throw new Error("Failed to switch mode");

        await fetchLatest();
    } catch (err) {
        console.error("Error switching mode:", err);
        alert("Failed to switch mode");
    }
}

async function sendValve() {
    const value = parseInt(valveSlider.value);

    try {
        const payload = JSON.stringify({ opening: value });
        const res = await fetch(ENDPOINT_VALVE, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: payload
        });

        if (!res.ok)
            throw new Error("Failed to set valve");

    } catch (err) {
        console.error("Error setting valve:", err);
        alert("Failed to set valve opening");
    }
}

valveSlider.addEventListener("input", (e) => {
    sliderValue.textContent = e.target.value + "%";
});

switchModeBtn.addEventListener("click", switchMode);
sendValveBtn.addEventListener("click", sendValve);

setInterval(fetchLatest, pollIntervalMs);
fetchLatest();