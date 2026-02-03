# CUS Architecture - Transport-Agnostic Event-Driven System

## 🎯 Principio Fondamentale

**Il Controller esprime INTENZIONI, non implementazioni.**

Controller dice:
- "Voglio impostare la valvola al 50%" → pubblica evento `valve.set`
- "Ho ricevuto un livello acqua" → riceve evento `tank.level`

**NON sa** se i comandi vanno via Serial, MQTT, HTTP, WebSocket, etc.

---

## 📊 Architettura Attuale

```
┌─────────────────────────────────────────────────────┐
│            EventDispatcher (Message Bus)            │
│                                                      │
│  Eventi Domain:                                      │
│  - tank.level      (input: livello acqua)           │
│  - wcs.status      (input: stato Arduino)           │
│  - valve.set       (output: comando valvola)        │
│  - alarm.set       (output: comando allarme)        │
└──────────┬─────────────────────┬────────────────────┘
           │                     │
    ┌──────▼──────┐       ┌──────▼──────┐
    │  MQTT Svc   │       │ Serial Svc  │
    │ (Receiver)  │       │ (Handler)   │
    │             │       │             │
    │ Pubblica:   │       │ Pubblica:   │
    │ tank.level  │       │ wcs.status  │
    │             │       │             │
    │             │       │ Ascolta:    │
    │             │       │ valve.set   │
    │             │       │ alarm.set   │
    └─────────────┘       └─────────────┘

    ┌─────────────────────────────┐
    │   SystemController          │
    │   (Business Logic)          │
    │                             │
    │   Ascolta:                  │
    │   - tank.level              │
    │   - wcs.status              │
    │                             │
    │   Pubblica:                 │
    │   - valve.set               │
    │   - alarm.set               │
    └─────────────────────────────┘
```

---

## 🔄 Esempio: Cambio Trasporto SENZA Toccare Controller

### Scenario 1: Arduino usa Serial (ATTUALE)

```python
# main.py
serial_service = SerialService(...)
serial_service.register_command_handlers(event_dispatcher)  # Ascolta valve.set

services = [mqtt_service, serial_service, http_service]
controller = SystemController(model, services, event_dispatcher)
```

**Flusso:**
```
Controller → publish("valve.set", 50) 
           → EventDispatcher 
           → SerialService._on_valve_command()
           → Arduino via porta seriale
```

---

### Scenario 2: Arduino passa a MQTT (FUTURO)

```python
# main.py (SOLO QUESTO FILE CAMBIA!)
mqtt_command_service = MQTTCommandService(  # Nuovo servizio
    event_dispatcher,
    broker="broker.mqtt.com",
    command_topic="arduino/commands"
)
mqtt_command_service.register_command_handlers(event_dispatcher)  # Ascolta valve.set

# SerialService non viene più aggiunto alla lista
services = [mqtt_service, mqtt_command_service, http_service]
controller = SystemController(model, services, event_dispatcher)  # STESSO CONTROLLER!
```

**Flusso:**
```
Controller → publish("valve.set", 50)  # IDENTICO!
           → EventDispatcher 
           → MQTTCommandService._on_valve_command()  # Nuovo handler
           → Arduino via MQTT broker
```

**Controller NON è stato modificato!** ✅

---

### Scenario 3: Doppio Trasporto (Serial + MQTT)

```python
# main.py
serial_service = SerialService(...)
serial_service.register_command_handlers(event_dispatcher)

mqtt_command_service = MQTTCommandService(...)
mqtt_command_service.register_command_handlers(event_dispatcher)

services = [mqtt_service, serial_service, mqtt_command_service, http_service]
controller = SystemController(model, services, event_dispatcher)
```

**Risultato**: 
- Un comando `valve.set` viene eseguito su **ENTRAMBI** Serial e MQTT
- Controller: **NESSUNA MODIFICA** ✅

---

## 🔌 Come Aggiungere un Nuovo Trasporto

### Esempio: WebSocket per Comandi

1. **Crea nuovo servizio** (il Controller NON cambia):

```python
# websocket_service.py
class WebSocketService(BaseService):
    async def _on_valve_command(self, event: Event):
        position = event.payload["position"]
        await self.ws.send(json.dumps({"valve": position}))
    
    def register_command_handlers(self, dispatcher):
        dispatcher.subscribe("valve.set", self._on_valve_command)
        dispatcher.subscribe("alarm.set", self._on_alarm_command)
```

2. **Aggiungi in main.py** (il Controller NON cambia):

```python
ws_service = WebSocketService(event_dispatcher, url="ws://arduino.local")
ws_service.register_command_handlers(event_dispatcher)
services.append(ws_service)
```

**Controller rimane identico!** ✅

---

## ✨ Benefici Ottenuti

1. ✅ **Sostituibilità**: Cambi Serial → MQTT senza toccare business logic
2. ✅ **Testabilità**: Mock EventDispatcher, non ogni servizio
3. ✅ **Estendibilità**: Aggiungi trasporti senza modificare Controller
4. ✅ **Multi-transport**: Un comando va su più canali simultaneamente
5. ✅ **Disaccoppiamento**: Controller non importa né MQTT né Serial né HTTP

---

## 📝 Contratto Eventi Domain

### Input Events (→ Controller)
- `tank.level` - Livello acqua (da MQTT/Serial/HTTP)
- `wcs.status` - Stato WCS (da Serial/MQTT)

### Output Events (← Controller)
- `valve.set` - Imposta valvola `{position: float}`
- `alarm.set` - Imposta allarme `{active: bool}`
- `system.status.request` - Richiedi stato completo

**Qualsiasi servizio può pubblicare input o ascoltare output.**

---

## 🎓 Conclusione

L'EventDispatcher trasforma il sistema da:
- "Controller comanda direttamente Serial" ❌
  
A:
- "Controller esprime intenzioni, qualcuno le realizza" ✅

**Risultato**: Architettura modulare, sostituibile, testabile, estendibile.
