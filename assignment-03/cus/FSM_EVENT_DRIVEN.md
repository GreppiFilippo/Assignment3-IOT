# FSM Event-Driven con PyPubSub - Guida Completa

## 🎯 Cos'è una FSM Event-Driven?

Invece di controllare continuamente le condizioni nel loop (polling):
```python
# ❌ POLLING (vecchio)
while True:
    if level > THRESHOLD:
        state = ALARM
    await asyncio.sleep(0.1)
```

Usiamo **eventi** che scatenano transizioni atomiche:
```python
# ✅ EVENT-DRIVEN (nuovo)
bus.subscribe("sensor.level", _on_level_change)  # Reagisci quando accade!

def _on_level_change(level):
    if level > THRESHOLD:
        self._transition_to(SystemState.ALARM)
```

---

## 📊 Architettura FSM - Event-Driven

```
┌─────────────────────────────────────────────────────────┐
│            PyPubSub EventBus (Message Broker)           │
└──────────────────────────────────────────────────────────┘
                    ▲                         ▲
                    │ sensor.level            │ button.pressed
                    │ (40cm, 60cm, 90cm)      │ (press)
                    │                         │
    ┌───────────────┴─────────┐      ┌────────┴──────┐
    │   Serial/MQTT Service    │      │ Button Input  │
    │   (Publishes levels)     │      │   (UI/HW)     │
    └─────────────────────────┘      └───────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  TankController FSM  │ ◄─── LISTENS
        │  (Event-Driven)      │
        │                      │
        │ _on_level_event()    │
        │ _on_button_pressed() │
        │ _on_manual_valve()   │
        └──────────┬───────────┘
                   │
                   ▼ PUBLISHES
        ┌──────────────────────┐
        │   cmd.valve          │ ──► Serial ──► Arduino
        │   (opening: 0-100%)  │
        └──────────────────────┘
```

---

## 🔄 Flusso Completo: Esempio Pratico

### Scenario: Livello aumenta da 30cm a 85cm

```
1️⃣  EVENTO: sensor.level(level=85) pubblicato dalla SerialService
    └─ Arduino legge potenziomentro → JSON: {"POT_VAL": 85}
    └─ SerialService parsa e pubblica: bus.publish("sensor.level", level=85)

2️⃣  REAZIONE: TankController._on_level_event() scattata
    └─ Update: self._current_level = 85
    └─ Check: 85 >= L2_THRESHOLD (80) → ALARM state!
    └─ Transition: NORMAL → ALARM
    └─ Action: _publish_valve_command(ALARM) → 100%

3️⃣  COMANDO: cmd.valve(opening=100) pubblicato
    └─ SerialService._on_valve_command() scattata
    └─ Invia JSON: {"VALVE": 100} via UART → Arduino

4️⃣  HARDWARE: Arduino apre valvola al 100%
    └─ Livello inizia a scendere lentamente...

5️⃣  NUOVO EVENTO: sensor.level(level=75)
    └─ TankController valuta: 75 < L2 (80) → PRE_ALARM
    └─ Transition: ALARM → PRE_ALARM
    └─ Command: cmd.valve(opening=50)

6️⃣  ... ciclo continua event-driven
```

---

## 🌳 State Machine Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      UNCONNECTED                             │
│  (Waiting for first sensor reading)                          │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ sensor.level received
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      AUTOMATIC                               │
│  Selects sub-state based on water level thresholds:          │
│  L1=50cm (warning), L2=80cm (critical)                       │
│                                                              │
│  Sub-states:                                                 │
│  ┌─────────────┐      ┌──────────────┐      ┌──────────┐   │
│  │   NORMAL    │◄────►│   TRACKING   │─────►│PRE_ALARM │   │
│  │ (0% valve)  │      │ PRE_ALARM    │      │(50%)     │   │
│  └─────────────┘      │(T1=5s timer) │      └────┬─────┘   │
│       ▲               └──────────────┘           │         │
│       │                                          ▼         │
│       └──────────────────────────────────────┌────────┐    │
│                                              │ ALARM  │    │
│                                              │(100%)  │    │
│                                              └────────┘    │
└────────────────┬──────────────────────────────────────────┘
                 │ button.pressed
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                       MANUAL                                 │
│  (User controls valve directly via manual.valve_command)     │
│  Valve: 0-100% at user discretion                            │
└─────────────────┬────────────────────────────────────────────┘
                  │ button.pressed
                  ▼
          Back to AUTOMATIC
```

---

## 📋 Eventi Domain e Handlers

### Input Events (→ Controller)

| Evento | Parametri | Sorgente | Effetto |
|--------|-----------|---------|---------|
| `sensor.level` | `level: float` | Serial/MQTT | Valuta transizioni AUTOMATIC sub-states |
| `button.pressed` | - | UI/Hardware | Toggle AUTOMATIC ↔ MANUAL |
| `manual.valve_command` | `opening: float` | HTTP/UI | (Solo in MANUAL) → cmd.valve |
| `system.timeout` | - | Internal | AUTOMATIC/MANUAL → UNCONNECTED (T2=10s) |

### Output Events (← Controller)

| Evento | Parametri | Destinazione | Significato |
|--------|-----------|-------------|------------|
| `cmd.valve` | `opening: 0-100` | Serial → Arduino | Comanda apertura valvola |
| `config.MODE` | `state: SystemState` | MQTT → Cloud | Pubblica stato attuale |

---

## 💾 Implementazione Tecnica

### 1️⃣ Sottoscrizione agli Eventi (nel `__init__`)

```python
class TankController(BaseService):
    def __init__(self, event_bus: EventBus):
        super().__init__("tank_controller", event_bus)
        
        # FSM state
        self._system_state = SystemState.UNCONNECTED
        self._automatic_state = AutomaticState.NORMAL
        
        # ✅ Subscribe to events
        self.bus.subscribe("sensor.level", self._on_level_event)
        self.bus.subscribe("button.pressed", self._on_button_pressed)
        self.bus.subscribe("manual.valve_command", self._on_manual_valve)
```

### 2️⃣ Handler per Transizioni

```python
def _on_level_event(self, **kwargs):
    """Event handler: sensor.level received"""
    level = kwargs.get("level", 0.0)
    self._current_level = level
    self._last_level_timestamp = int(time.monotonic() * 1000)
    
    # Transition: UNCONNECTED → AUTOMATIC
    if self._system_state == SystemState.UNCONNECTED:
        self._transition_to(SystemState.AUTOMATIC, AutomaticState.NORMAL)
        self.bus.publish(config.MODE, state=SystemState.AUTOMATIC)
        return
    
    # Evaluate sub-state based on level
    if self._system_state == SystemState.AUTOMATIC:
        self._evaluate_automatic_state(level)
```

### 3️⃣ Valutazione Sub-stati

```python
def _evaluate_automatic_state(self, level: float):
    """Match level thresholds and transition sub-states"""
    current = self._automatic_state
    new_state = current
    
    match current:
        case AutomaticState.NORMAL:
            if config.L1_THRESHOLD < level < config.L2_THRESHOLD:
                new_state = AutomaticState.TRACKING_PRE_ALARM
            elif level >= config.L2_THRESHOLD:
                new_state = AutomaticState.ALARM
        
        case AutomaticState.TRACKING_PRE_ALARM:
            if level <= config.L1_THRESHOLD:
                new_state = AutomaticState.NORMAL
            elif level >= config.L2_THRESHOLD:
                new_state = AutomaticState.ALARM
            # Also check timeout T1
            elif self._elapsed_time() > config.T1_DURATION * 1000:
                new_state = AutomaticState.PRE_ALARM
        
        # ... altri casi
    
    # Se lo stato è cambiato, pubblica comando
    if new_state != current:
        self._transition_to(self._system_state, new_state)
        self._publish_valve_command(new_state)
```

### 4️⃣ Comando della Valvola

```python
def _publish_valve_command(self, sub_state: AutomaticState):
    """Publish valve opening based on sub-state"""
    match sub_state:
        case AutomaticState.NORMAL:
            opening = 0.0          # Chiusa
        case AutomaticState.TRACKING_PRE_ALARM:
            opening = 25.0         # Pre-apertura
        case AutomaticState.PRE_ALARM:
            opening = 50.0         # Meta apertura
        case AutomaticState.ALARM:
            opening = 100.0        # Apertura massima
    
    self.bus.publish("cmd.valve", opening=opening)
```

---

## ⏱️ Timing: T1 e T2 Timeouts

### T1_DURATION (5 secondi)
- **Quando**: Mentre si è in TRACKING_PRE_ALARM
- **Se**: Livello rimane tra L1 e L2 per >5s
- **Allora**: Transizione → PRE_ALARM (apri al 50%)
- **Reason**: Protezione: se il livello non scende, apri di più

### T2_TIMEOUT (10 secondi) 
- **Quando**: Non ricevi sensor.level da >10s
- **Allora**: Transizione → UNCONNECTED
- **Reason**: Protezione: se Arduino non risponde, disconnetti

```python
async def run(self):
    """Periodic check for timeouts (non-blocking)"""
    while self._running:
        now = int(time.monotonic() * 1000)
        if now - self._last_level_timestamp > config.T2_TIMEOUT * 1000:
            if self._system_state != SystemState.UNCONNECTED:
                self._transition_to(SystemState.UNCONNECTED)
        
        await asyncio.sleep(1.0)  # Only wake every 1 second
```

---

## 🔌 Come Integrare Nuovi Eventi

### Esempio: Aggiungere un sensore di temperatura

1. **Definisci il nuovo evento in config**:
```python
# config.py
SENSOR_EVENTS = {
    "sensor.level": "water_level",
    "sensor.temperature": "water_temperature",
}
```

2. **Aggiungi subscriber nel controller**:
```python
# tank_controller.py __init__
self.bus.subscribe("sensor.temperature", self._on_temperature_event)
```

3. **Implementa handler**:
```python
def _on_temperature_event(self, **kwargs):
    temp = kwargs.get("temperature", 0.0)
    if temp > 40:
        logger.warning(f"High temperature: {temp}°C")
        # Trigger alarm logic
```

4. **Configura la pubblicazione nel service**:
```python
# serial_service.py
serial_service.configure_messaging(
    pub_topics={
        "POT_VAL": "sensor.level",
        "TEMP": "sensor.temperature"  # ✅ Nuovo!
    }
)
```

---

## 📊 Vantaggi della FSM Event-Driven

| Aspetto | Polling (Vecchio) | Event-Driven (Nuovo) |
|--------|---------|------------|
| **Latenza** | Fino a 100ms (sleep time) | <1ms (immediato) |
| **CPU Usage** | Alto (loop continuo) | Basso (reactive) |
| **Testabilità** | Difficile (timing-dependent) | Facile (mock events) |
| **Estendibilità** | Nuovo if/else nel loop | Nuovo subscriber |
| **Debugging** | Stampe nel loop | Traccia chiara degli eventi |
| **Scalabilità** | N stati = O(N) if/else | N eventi = O(1) match |

---

## 🧪 Testing dell'FSM

### Test Unitario: Transizione UNCONNECTED → AUTOMATIC

```python
async def test_level_connects_system():
    bus = EventBus()
    controller = TankController(bus)
    
    assert controller.state == SystemState.UNCONNECTED
    
    # Simula evento
    bus.publish("sensor.level", level=45.0)
    await asyncio.sleep(0.01)  # Let handler execute
    
    # Verifica transizione
    assert controller.state == SystemState.AUTOMATIC
    assert controller.current_level == 45.0
```

### Test Integrazione: Livello → Valvola

```python
async def test_level_90_opens_valve_100():
    bus = EventBus()
    controller = TankController(bus)
    valve_commands = []
    
    # Intercetta comandi valvola
    bus.subscribe("cmd.valve", lambda **kw: valve_commands.append(kw))
    
    # Simula livello alto
    bus.publish("sensor.level", level=90.0)
    await asyncio.sleep(0.01)
    
    # Verifica comando
    assert len(valve_commands) == 1
    assert valve_commands[0]["opening"] == 100.0
```

---

## 🚀 Come Eseguire

```bash
# Avvia il sistema
./runcus.sh
# o
python src/main.py
```

**Log attesi**:
```
INFO | TankController FSM initialized
INFO |   Subscribes to: sensor.level, button.pressed, manual.valve_command
INFO | 🚀 Starting all system services...
INFO | [tank_controller] FSM initialized: UNCONNECTED
INFO | [serial_service] Port COM3 opened successfully
INFO | [mqtt_service] Connected to broker
DEBUG | [serial_service] Published POT_VAL → sensor.level: 45.5
INFO | [tank_controller] Level received (45.5cm) - UNCONNECTED → AUTOMATIC
```

---

## 📚 Riferimenti

- **PyPubSub**: https://pypubsub.readthedocs.io/
- **State Machines**: https://en.wikipedia.org/wiki/Finite-state_machine
- **Event-Driven Architecture**: https://martinfowler.com/articles/201701-event-driven.html
