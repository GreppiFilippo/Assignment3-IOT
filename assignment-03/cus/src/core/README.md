# TankController - Hierarchical State Pattern

## 📁 Struttura File

```
src/core/
├── tank_controller.py          # Orchestratore minimale (93 righe)
├── system_states.py            # SystemState: UNCONNECTED, MANUAL, AUTOMATIC
└── automatic_substates.py      # AutomaticSubStates: NORMAL, TRACKING, PRE_ALARM, ALARM
```

## 🎯 Architettura

### TankController (Orchestratore)
**Responsabilità:**
- Mantiene `current_state: SystemStateBase`
- Storicizza `water_levels: List[LevelReading]`
- Delega eventi agli stati

**NON fa:**
- ❌ Logica di transizione
- ❌ Calcoli di threshold
- ❌ Gestione timer
- ❌ Pubblicazione comandi

### SystemState (3 stati)
1. **UnconnectedState**: Attende primo livello → transizione ad AUTOMATIC
2. **ManualState**: Controllo manuale operatore, pubblica cmd.valve
3. **AutomaticState**: Container per sottostati automatici

### AutomaticSubState (4 sottostati)
1. **NormalSubState**: 0% valvola, monitora L1
2. **TrackingPreAlarmSubState**: 25% valvola, timer T1
3. **PreAlarmSubState**: 50% valvola
4. **AlarmSubState**: 100% valvola (livello critico)

## 🔄 Flusso Eventi

```python
# Evento: sensor.level
EventBus → TankController._on_level_event()
         → water_levels.append(reading)           # Storicizzazione
         → current_state.handle_level_event()     # Delegazione
         → (se AutomaticState)
           → current_substate.evaluate_transition()  # Logica nello stato
           → (se transizione)
             → new_substate.on_enter()              # Pubblica cmd.valve
```

## 🚀 Estendere il Sistema

### Aggiungere Nuovo System State

```python
# 1. Crea file: src/core/custom_states.py
from core.system_states import SystemStateBase
from models.schemas import SystemState as SystemStateEnum

class EmergencyStopState(SystemStateBase):
    def get_state_name(self) -> SystemStateEnum:
        return SystemStateEnum.EMERGENCY  # Aggiungi in schemas.py
    
    def handle_level_event(self, level, timestamp, controller):
        # Ignora livelli durante emergenza
        pass
    
    def handle_button_pressed(self, controller):
        # Reset emergenza
        controller.transition_to(AutomaticState())
    
    def on_enter(self, controller):
        # Chiudi valvola immediatamente
        controller.bus.publish("cmd.valve", opening=0.0)

# 2. Usa da altri stati
class AlarmSubState:
    def evaluate_transition(self, level, elapsed_ms):
        if level > EXTREME_THRESHOLD:
            return EmergencyStopState()  # Trigger emergency
```

### Aggiungere Nuovo SubState Automatico

```python
# 1. In automatic_substates.py
class CriticalSubState(AutomaticSubStateBase):
    def get_state_name(self) -> AutomaticStateEnum:
        return AutomaticStateEnum.CRITICAL
    
    def get_valve_opening(self) -> float:
        return 75.0  # Custom opening
    
    def evaluate_transition(self, level, elapsed_ms):
        if level <= config.L2_THRESHOLD:
            return PreAlarmSubState()
        elif level >= EXTREME_THRESHOLD:
            return AlarmSubState()
        return None

# 2. Usa da altri substates
class PreAlarmSubState:
    def evaluate_transition(self, level, elapsed_ms):
        if config.L2_THRESHOLD < level < EXTREME_THRESHOLD:
            return CriticalSubState()  # Nuovo sottostato
```

## 🧪 Testing

### Test Singolo Stato (Unit Test)

```python
def test_normal_to_tracking():
    state = NormalSubState()
    new_state = state.evaluate_transition(level=35, elapsed_ms=0)
    assert isinstance(new_state, TrackingPreAlarmSubState)

def test_alarm_valve_opening():
    state = AlarmSubState()
    assert state.get_valve_opening() == 100.0
```

### Test TankController (Integration Test)

```python
bus = EventBus()
controller = TankController(bus)

# Test transizione base
assert controller.state == SystemState.UNCONNECTED
bus.publish('sensor.level', level=10.0, timestamp=1000)
assert controller.state == SystemState.AUTOMATIC

# Test storicizzazione
assert len(controller.water_levels) == 1
assert controller.current_level == 10.0
```

## 📊 Benefici

| Principio | Come è Rispettato |
|-----------|-------------------|
| **SRP** | Ogni stato gestisce solo la propria logica |
| **OCP** | Nuovi stati senza modificare esistenti |
| **LSP** | Tutti gli stati sono intercambiabili |
| **ISP** | Interfacce separate (SystemState vs SubState) |
| **DIP** | TankController dipende da abstraction |

## 📝 Metriche

- **Righe TankController**: 93 (-51% rispetto a prima)
- **Responsabilità TankController**: 3 (vs 7)
- **Classi totali**: 10 (vs 1)
- **Testabilità**: Unit tests isolati ✅

## 🔗 Riferimenti

- `SOLID_COMPLIANCE.md`: Spiegazione dettagliata di come ogni principio SOLID è rispettato
- `ARCHITECTURE.md`: Architettura event-driven complessiva del sistema
