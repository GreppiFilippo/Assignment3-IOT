#ifndef __MQTT_SERVICE__
#define __MQTT_SERVICE__

#include <PubSubClient.h>
#include <WiFiClient.h>

#include "kernel/services/ConnectionService.hpp"

#define MAX_MQTT_TOPICS 5

class MqttService : public ConnectionService
{
   private:
    const char* broker;
    int port;
    const char* clientId;
    const char* topics[MAX_MQTT_TOPICS];
    PubSubClient* mqttClient;
    WiFiClient* espClient;

   public:
    MqttService(const char* broker, int port, const char* clientId);
    void init() override;
    void connect() override;
    void send(const char* data, size_t length);
    void setTopic(const char* topic);
};

#endif  // __MQTT_SERVICE__
