#ifndef __MQTT_SERVICE__
#define __MQTT_SERVICE__

#include <PubSubClient.h>
#include <WiFi.h>

#include "kernel/services/ProtocolService.hpp"

class MqttService : public ProtocolService
{
   private:
    const char* broker;
    int port;
    const char* clientId;
    WiFiClient espClient;

    PubSubClient mqttClient;

   public:
    MqttService(NetworkConnectionService* networkService, const char* broker, int port,
                const char* clientId);

    void init() override;
    void connect() override;
    bool send(Message* msg) override;
    void loop() override;
};

#endif
