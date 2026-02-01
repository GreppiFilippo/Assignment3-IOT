#ifndef CONFIG_HPP
#define CONFIG_HPP

/***********************
 * PIN CONFIGURATION
 ***********************/
#define SONAR_TRIG_PIN 5
#define SONAR_ECHO_PIN 18
#define LED_GREEN_PIN 2
#define LED_RED_PIN 4

/***********************
 * SONAR PARAMETERS
 ***********************/
#define SONAR_MAX_DISTANCE_CM 200
#define SONAR_TIMEOUT_US 30000  // microsecondi

/***********************
 * SAMPLING PARAMETERS
 ***********************/
#define SAMPLING_INTERVAL_MS 1000  // intervallo di campionamento in millisecondi

/***********************
 * MQTT CONFIGURATION
 ***********************/
#define MQTT_BROKER "192.168.1.100"
#define MQTT_PORT 1883
#define MQTT_TOPIC_LEVEL "tank/level"
#define MQTT_TOPIC_STATUS "tank/status"
#define MQTT_CLIENT_ID "ESP32_TMS"

/***********************
 * THRESHOLDS & TIMERS
 ***********************/
#define LEVEL_L1 50    // cm, soglia per apertura parziale
#define LEVEL_L2 80    // cm, soglia per apertura completa
#define TIME_T1 30000  // ms, tempo sopra L1 prima di aprire parzialmente
#define TIME_T2 10000  // ms, timeout rete prima di entrare in UNCONNECTED

/***********************
 * LED STATES
 ***********************/
#define HIGH
#define LOW

/***********************
 * FSM STATES
 ***********************/
#define STATE_INIT 0
#define STATE_AUTOMATIC 1
#define STATE_MANUAL 2
#define STATE_ERROR 3

/***********************
 * SERIAL CONFIGURATION
 ***********************/
#define BAUD 115200

#define SENDING_BUFFER_SIZE 256

#endif  // CONFIG_HPP