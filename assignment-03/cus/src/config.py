"""Configuration settings for the CUS system."""

# === MQTT Configuration ===
MQTT_BROKER_HOST = "broker.mqtt-dashboard.com"
MQTT_BROKER_PORT = 1883

LEVEL_IN_TOPIC = "level_in"
LEVELS_OUT_TOPIC = "level_out"
POT_TOPIC = "pot"
MODE_TOPIC = "mode"
MODE_CHANGE_TOPIC = "btn"
OPENING_TOPIC = "valve"

SERIAL_SEND_INTERVAL=0.5  # Time interval to send data to Arduino (in seconds)


# === Serial Configuration ===
SERIAL_PORT = "/dev/cu.usbmodem14101"  # Change to "/dev/ttyUSB0" on Linux/Mac
SERIAL_BAUDRATE = 115200

# === HTTP Configuration ===
HTTP_HOST = "localhost"
HTTP_PORT = 8000
ALLOWED_ORIGINS = ["http://127.0.0.1:8080", "http://localhost:8080"] 
ALLOWED_CREDENTIALS = True
ALLOWED_METHODS = ["*"]
ALLOWED_HEADERS = ["*"]

# === System Configuration ===
# Water Level Thresholds (in cm)
L1_THRESHOLD = 0.30  # First warning level
L2_THRESHOLD = 0.5  # Critical level
MAX_READINGS = 100  # Maximum number of water level readings to store

# Timing Configuration (in seconds)
T1_DURATION = 5.0   # Time to wait before opening valve at 50%
T2_TIMEOUT = 10.0   # Timeout for considering system UNCONNECTED

# === Logging Configuration ===
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "logs/cus.log"
