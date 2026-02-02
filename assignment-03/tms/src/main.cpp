#include <esp32-hal.h>

#include "config.hpp"
#include "devices/Led.hpp"
#include "devices/Sonar.hpp"
#include "kernel/Logger.hpp"
#include "kernel/TaskRunner.hpp"
#include "kernel/services/MqttService.hpp"
#include "kernel/services/WiFiConnectionService.hpp"
#include "model/Context.hpp"
#include "model/HWPlatform.hpp"
#include "tasks/NetworkTask.hpp"
#include "tasks/SensorsTask.hpp"

Context* pContext;
HWPlatform* pHWPlatform;

void setup()
{
    Serial.begin(BAUD_RATE);

    pContext = new Context();

    pHWPlatform = new HWPlatform();
    pHWPlatform->init();

    // ==== NETWORK LAYER INIT ====
    WiFiConnectionService* pWiFiService = new WiFiConnectionService(WIFI_SSID, WIFI_PASSWORD);
    pWiFiService->init();

    // ==== PROTOCOL LAYER INIT ====
    MqttService* pMqttService =
        new MqttService(pWiFiService, MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID);
    pMqttService->init();

    // ==== TASK INIT ====
    NetworkTask* pNetworkTask =
        new NetworkTask(pWiFiService, pMqttService, pHWPlatform->getAliveLight(),
                        pHWPlatform->getErrorLight(), pContext);
    pNetworkTask->init();

    SensorsTask* pSensorsTask = new SensorsTask(pContext, pHWPlatform->getProximitySensor());
    pSensorsTask->init();

    TaskRunner* pNetworkTaskRunner =
        new TaskRunner(pNetworkTask, "NetworkTask", 4096, 1, pdMS_TO_TICKS(1000), 1);

    TaskRunner* pSensorsTaskRunner = new TaskRunner(pSensorsTask, "SensorsTask", 4096, 1,
                                                    pdMS_TO_TICKS(SAMPLING_INTERVAL_MS), 1);

    Logger.log(F("TMS: Setup completed."));
}

void loop() {}
