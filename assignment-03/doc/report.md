# Assignment #03 - *Smart Tank Monitoring System*

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Subsystems](#subsystems)
   - [Tank Monitoring Subsystem (TMS)](#tank-monitoring-subsystem-tms)
   - [Water Channel Subsystem (WCS)](#water-channel-subsystem-wcs)
   - [Control Unit Subsystem (CUS)](#control-unit-subsystem-cus)
   - [Dashboard Subsystem (DBS)](#dashboard-subsystem-dbs)
4. [Communication Protocols](#communication-protocols)
5. [Hardware Schema](#hardware-schema)
6. [Demo Video](#demo-video)

---

## Introduction

The **Smart Tank Monitoring System** is a distributed IoT system for monitoring and controlling rainwater levels in a tank. The system automatically manages the opening of a valve to drain water into a channel network when the level exceeds certain thresholds.

### Project Objectives
- Continuous water level monitoring via sonar sensor
- Automatic/manual control of drainage valve
- Remote visualization of system state through web dashboard
- Error and disconnection condition handling

---

## System Architecture

The system consists of **4 independent subsystems** that communicate with each other:

![System Architecture](assignment-03-sketch.png)

### Operating Modes
- **AUTOMATIC**: The system automatically controls valve opening based on water level
- **MANUAL**: The operator manually controls opening via potentiometer or dashboard
- **UNCONNECTED**: Error state when TMS doesn't communicate with CUS for more than T₂

---


### Tank Monitoring Subsystem (TMS)

!["TMS wiring"](tms/schema.png)

**Features**:
- Continuous water level sampling at frequency F
- Data transmission to CUS via MQTT
- Connection status indication via LEDs:
  - **Green ON**: System working correctly
  - **Red ON**: Network problems

**Software Architecture**:
- Implementation based on **Finite State Machine (FSM)** and **RTOS tasks**
- Use of FreeRTOS for concurrent operation management
- Main tasks:
  - `SensorTask`: Periodic sonar reading
  - `MqttTask`: Data publishing and connection management
  - `LedTask`: LED indicator control

#### FSM - TMS
```
     ┌──────────────┐
     │  INIT        │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐       Network Error
     │  CONNECTED   │────────────────────┐
     │  (Green LED) │                    │
     └──────┬───────┘                    │
            │                            ▼
            │ Sample & Publish    ┌──────────────┐
            └────────►            │ DISCONNECTED │
                                  │  (Red LED)   │
                                  └──────┬───────┘
                                         │
                                         │ Network OK
                                         └────────────►
```

**Libraries Used**:
- PubSubClient (MQTT)
- WiFi (ESP32)
- NewPing (Sonar)

---

### Water Channel Subsystem (WCS)

**Hardware**: Arduino UNO, Servo motor, Potentiometer, Button, LCD I2C

**Features**:
- Valve opening control (0° = closed, 90° = 100% open)
- AUTOMATIC/MANUAL switch via button
- Manual control via potentiometer
- LCD display shows:
  - Valve opening percentage
  - Current operating mode

**Software Architecture**:
- **Task-based architecture** with cooperative scheduler
- Use of `TimerOne` for periodic scheduling
- Main tasks:
  - `ServoControlTask`: Servo position management
  - `ButtonTask`: Debouncing and press handling
  - `PotentiometerTask`: Analog input reading
  - `LCDTask`: Display update
  - `MsgTask`: Serial communication with CUS

#### FSM - WCS
```
           ┌──────────────┐
           │     INIT     │
           └──────┬───────┘
                  │
                  ▼
      ┌───────────────────────┐
      │     AUTOMATIC         │◄────────┐
      │  Servo controlled     │         │
      │     by CUS            │         │
      └───────────┬───────────┘         │
                  │                     │
         Button   │                     │ Button
         Press    │                     │ Press
                  ▼                     │
      ┌───────────────────────┐         │
      │      MANUAL           │─────────┘
      │  Servo controlled     │
      │  by Potentiometer     │
      └───────────────────────┘
```

**Libraries Used**:
- Servo
- LiquidCrystal_I2C
- TimerOne
- ArduinoJson (serial communication)

---

### Control Unit Subsystem (CUS)

**Platform**: PC/Server (Node.js / Python)

**Features**:
- **Policy Engine**: Implements control logic
  - L₁ < level < L₂ for T₁ → Valve 50%
  - Level > L₂ → Valve 100% immediately
- TMS communication timeout management (T₂)
- Coordination between all subsystems
- HTTP API for DBS
- MQTT-Serial bridge

**Communications**:
- **MQTT Broker**: Data reception from TMS
- **HTTP Server**: REST API for DBS
- **Serial**: Command transmission to WCS

**Technologies**:
- Runtime: Node.js / Python
- MQTT: Mosquitto broker or embedded
- HTTP: Express.js / Flask
- Serial: serialport / pyserial

#### FSM - CUS
```
       ┌──────────────┐
       │    IDLE      │
       └──────┬───────┘
              │
              ▼
    ┌─────────────────┐      No data for T₂
    │    NORMAL       │────────────────────┐
    │  Processing     │                    │
    │  data from TMS  │                    │
    └─────────┬───────┘                    │
              │                            ▼
              │ level > L₁          ┌──────────────┐
              ▼                     │ UNCONNECTED  │
    ┌─────────────────┐            │  Error State │
    │   ALARM_L1      │            └──────┬───────┘
    │  Valve 50%      │                   │
    └─────────┬───────┘                   │ Data received
              │                           └────────────►
              │ level > L₂
              ▼
    ┌─────────────────┐
    │   ALARM_L2      │
    │  Valve 100%     │
    └─────────────────┘
```

---

### Dashboard Subsystem (DBS)

**Platform**: Web Application (Browser)

**Features**:
- **Real-time chart**: Last N water level samples
- **Status visualization**:
  - Valve opening percentage
  - Operating mode (AUTOMATIC/MANUAL/UNCONNECTED/NOT AVAILABLE)
- **Controls**:
  - Switch button AUTOMATIC ↔ MANUAL
  - Slider for manual opening control

**Technologies**:
- Frontend: HTML5, CSS3, JavaScript
- Charting: Chart.js / D3.js
- Communication: Fetch API / WebSocket
- UI Framework: Bootstrap / Vue.js

**Structure**:
```html
┌────────────────────────────────────┐
│  Smart Tank Dashboard              │
├────────────────────────────────────┤
│  [Chart: Water Level History]      │
│                                    │
│  Status: AUTOMATIC ●               │
│  Valve Opening: 75% [=========   ] │
│                                    │
│  [Switch to MANUAL]                │
│  Manual Control: [==========] 50%  │
└────────────────────────────────────┘
```

---

## Communication Protocols

### MQTT (TMS ↔ CUS)
**Topic Structure**:
- `tank/sensor/level` - Water level publication (TMS → CUS)
- `tank/status` - Connection status (TMS → CUS)

**Payload Example** (JSON):
```json
{
  "level": 145,
  "timestamp": 1675234567,
  "unit": "cm"
}
```

### Serial (WCS ↔ CUS)
**Format**: JSON over Serial Line (9600 baud)

**Commands CUS → WCS**:
```json
{
  "cmd": "SET_VALVE",
  "value": 75
}
```

**Responses WCS → CUS**:
```json
{
  "mode": "AUTOMATIC",
  "valve": 75,
  "status": "OK"
}
```

### HTTP (DBS ↔ CUS)
**REST Endpoints**:
- `GET /api/status` - Complete system status
- `GET /api/history` - Water level history
- `POST /api/mode` - Change operating mode
- `POST /api/valve` - Set manual opening

---

## Hardware Schema

### TMS - ESP32
```
ESP32
├─ GPIO 14 ─► Sonar TRIG
├─ GPIO 12 ◄─ Sonar ECHO
├─ GPIO 25 ─► Green LED
├─ GPIO 26 ─► Red LED
└─ WiFi ───► MQTT Broker
```

### WCS - Arduino UNO
```
Arduino UNO
├─ Pin 9    ─► Servo Motor (PWM)
├─ Pin A0   ◄─ Potentiometer
├─ Pin 2    ◄─ Button (+ pull-up resistor)
├─ SDA/SCL  ─► LCD I2C
└─ Serial   ─► PC (CUS)
```

**[Insert breadboard/circuit diagram here]**

![Breadboard Schema](../assignment-03-sketch.png)

---

## Demo Video

**Demo video link**: [Insert YouTube/Drive link]

The video demonstrates:
1. System boot and subsystem connection
2. Automatic monitoring and valve opening when exceeding L₁
3. 100% opening when exceeding L₂
4. Switch to MANUAL mode via button/dashboard
5. Manual control via potentiometer
6. TMS disconnection handling (UNCONNECTED state)

---

## Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| F | 1 Hz | TMS sampling frequency |
| L₁ | 50 cm | Alert threshold level 1 |
| L₂ | 80 cm | Alert threshold level 2 |
| T₁ | 5 s | Time above L₁ before action |
| T₂ | 10 s | TMS disconnection timeout |
| N | 50 | Samples displayed in dashboard |

---

## Conclusions

The implemented system fulfills all required specifications, providing robust and distributed control of water level. The modular architecture allows easy maintenance and future extension. FSMs and concurrent tasks ensure deterministic behavior and system reactivity.

### Possible Future Developments
- Addition of multiple sensors for redundancy
- Implementation of ML-based predictive algorithms
- Mobile dashboard (Android/iOS app)
- Database logging for historical analysis

---

**Author**: [Student Name]  
**Student ID**: [Student ID Number]  
**Academic Year**: 2025/2026  
**Course**: Embedded Systems and IoT - ISI LT
