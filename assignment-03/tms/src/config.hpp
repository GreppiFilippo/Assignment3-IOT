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
#define SONAR_TIMEOUT_US 30000

/***********************
 * SAMPLING PARAMETERS
 ***********************/
#define SAMPLING_INTERVAL_MS 2000
#define NETWORK_INTERVAL_MS 1000

/***********************
 * WIFI CONFIGURATION
 ***********************/
#define WIFI_SSID "wifi"
#define WIFI_PASSWORD "psw"

/***********************
 * MQTT CONFIGURATION
 ***********************/
#define MQTT_BROKER "broker.mqtt-dashboard.com"
#define MQTT_PORT 1883
#define MQTT_TOPIC_LEVEL "tank/level"
#define MQTT_CLIENT_ID "ESP32_TMS"

/***********************
 * SERIAL CONFIGURATION
 ***********************/
#define BAUD_RATE 115200

#define SENDING_BUFFER_SIZE 256

#endif  // CONFIG_HPP