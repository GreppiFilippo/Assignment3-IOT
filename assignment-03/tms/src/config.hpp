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
#define SONAR_TIMEOUT_US 30000  // microseconds

/***********************
 * SAMPLING PARAMETERS
 ***********************/
#define SAMPLING_INTERVAL_MS 1000  // sampling interval in milliseconds

/***********************
 * WIFI CONFIGURATION
 ***********************/
#define WIFI_SSID "Redmi 10"
#define WIFI_PASSWORD "12345678"

/***********************
 * MQTT CONFIGURATION
 ***********************/
#define MQTT_BROKER "broker.mqtt-dashboard.com"
#define MQTT_PORT 1883
#define MQTT_TOPIC_LEVEL "tank/level"
#define MQTT_CLIENT_ID "ESP32_TMS"

/***********************
 * THRESHOLDS & TIMERS
 ***********************/
#define LEVEL_L1 50    // cm, threshold for partial opening
#define LEVEL_L2 80    // cm, threshold for full opening
#define TIME_T1 30000  // ms, time above L1 before partial opening
#define TIME_T2 10000  // ms, network timeout before entering UNCONNECTED

/***********************
 * SERIAL CONFIGURATION
 ***********************/
#define BAUD_RATE 115200

#define SENDING_BUFFER_SIZE 256

#endif  // CONFIG_HPP