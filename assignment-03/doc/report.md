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

The **Smart Tank Monitoring System** is a distributed IoT system for monitoring and controlling rainwater levels in a tank. The system automatically manages the opening of a valve to drain water into a channel network when the level exceeds certain thresholds or allows manual control via a web dashboard or a physical potentiometer. The system also provides real-time visualization of water levels and valve status.

## System Architecture

The system consists of **4 independent subsystems** that communicate with each other:

![System Architecture](assignment-03-sketch.png)

### Operating Modes
- **AUTOMATIC**: The system automatically controls valve opening based on water level
- **MANUAL**: The operator manually controls opening via potentiometer or dashboard
- **UNCONNECTED**: Error state when TMS doesn't communicate with CUS for more than T₂

---


### Tank Monitoring Subsystem (TMS)

**Platform**: ESP32 with FreeRTOS

!["TMS wiring"](tms/schema.png)

**Hardware Components**:
- Sonar sensor (HC-SR04) for water level measurement
- Green LED (alive/connection OK indicator)
- Red LED (error/network problem indicator)

**Software Architecture**:
Two independent tasks running on FreeRTOS:

1. **SensorsTask**: Samples water level periodically and stores data in shared context
2. **NetworkTask**: FSM managing WiFi/MQTT connection and data transmission

**Network Task FSM**:

![Network Task FSM](tms/network_task.svg)

**States**:
- **CONNECTING**: Establishing WiFi and MQTT connection
- **NETWORK_OK**: Connected, transmitting data (Green LED ON)
- **NETWORK_ERROR**: Connection lost, attempting reconnect (Red LED ON)



### Water Channel Subsystem (WCS)

**Platform**: Arduino UNO with cooperative scheduler

!["WCS wiring"](wcs/schema.png)

**Hardware Components**:
- Servo motor (valve control, 0° = closed, 90° = 100% open)
- Push button (mode switch)
- Potentiometer (manual valve control)
- LCD display (16x2)

**Software Architecture**:
Task-based architecture with 4 cooperative tasks:

1. **SystemTask**: FSM managing connection state (UNCONNECTED/CONNECTED) and mode switching
2. **ValveTask**: FSM controlling servo motor movement (IDLE/MOVING)
3. **MsgTask**: Serial communication with CUS (JSON commands/events)
4. **LCDTask**: Updates LCD display with valve position and mode

**System Task FSM**:

![System Task FSM](wcs/system_task.svg)

**States**:
- **UNCONNECTED**: No CUS communication, potentiometer controls valve
- **CONNECTED**: CUS commands control valve, displays AUTOMATIC/MANUAL mode

**Valve Task FSM**:

![Valve Task FSM](wcs/valve_task.svg)

**States**:
- **IDLE**: Servo off, waiting for position change
- **MOVING**: Servo active, moving to target position

### Control Unit Subsystem (CUS)

Built as event-driven microservice architecture using Python's asyncio framework.
It uses the state pattern to implement the control policy for valve management based on TMS data and operator input.
It is composed by a central event bus using the pub/sub pattern, and the services:
Tank Service is the core FSM implementing the control policy, while the others are responsible for communication with the other subsystems (SerialService for WCS, MQTTService for TMS, HttpService for DBS).

**Platform**: Python (asyncio-based architecture)

**Architecture Components**:
1. **EventBus**: Pub/sub message broker for inter-service communication
2. **TankService**: Core FSM implementing control policy
3. **SerialService**: JSON communication with WCS via serial port
4. **MQTTService**: Level data reception from TMS
5. **HttpService**: REST API (FastAPI) for DBS

**TankService FSM**:

![CUS FSM](cus/tank_service_fsm.svg)

**System States**:
- **UNCONNECTED**: No TMS data received, waiting for first level reading
- **AUTOMATIC**: FSM controls valve with 4 substates:
  - **NORMAL**: Level OK, valve 0%
  - **TRACKING_PRE_ALARM**: L1 < level < L2, starting T1 timer
  - **PRE_ALARM**: T1 expired, valve 50%
  - **ALARM**: Level ≥ L2, valve 100%
- **MANUAL**: Operator controls valve via potentiometer/dashboard

**Transitions**:
- Button press toggles AUTOMATIC ↔ MANUAL
- T2 timeout (no TMS data) → UNCONNECTED from any state

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


## Demo Video

[Watch the demonstration video](https://liveunibo-my.sharepoint.com/:v:/g/personal/filippo_greppi2_studio_unibo_it/IQDeM8AzXj4vT530_44pwb-SAQ6p9UIpJB-1nDFXG11v5kQ?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=RQHUjg)

