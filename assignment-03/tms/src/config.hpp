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
 * WIFI CONFIGURATION
 ***********************/
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

/***********************
 * MQTT CONFIGURATION
 ***********************/
#define MQTT_BROKER "broker.hivemq.com"
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
 * SERIAL CONFIGURATION
 ***********************/
#define BAUD_RATE 115200

#define SENDING_BUFFER_SIZE 256

#endif  // CONFIG_HPP