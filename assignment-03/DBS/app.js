const N = 60;
const pollIntervalMs = 2000;
const labels = [];
const values = [];

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
            tension: 0.2
        }]
    },
    options: {
        responsive: true,
        animation: {
            duration: 0
        },
        scales: {
            x: {
                type: "time",
                time: {
                    tooltipFormat: "HH:mm:ss",
                    displayFormats: {
                        second: "HH:mm:ss"
                    }
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
        const res = await fetch(`/api/readings?limit=${N}`);
        if (!res.ok) throw new Error(res.status);

        const data = await res.json();

        labels.length = 0;
        values.length = 0;

        data.forEach(p => {
            labels.push(new Date(p.ts));
            values.push(p.value);
        });

        chart.update();

        const statusRes = await fetch("/api/status");
        const st = await statusRes.json();

        systemState.textContent =
            st.mode ?? State.NOT_AVAILABLE;

        valveOpening.textContent =
            `${st.valve ?? "--"}`;

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
        const res = await fetch("/api/mode", {
            method: "POST"
        });
        
        if (!res.ok) 
            throw new Error("Failed to switch mode");
        
        await fetchLatest();
    } catch (err) {
        console.error("Error switching mode:", err);
        alert("Failed to switch mode");
    }
}

async function sendValve() {
    const value = parseInt(valveSlider.value);
    
    try {
        const res = await fetch("/api/valve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ opening: value })
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