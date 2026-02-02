#include "kernel/services/MqttService.hpp"

#include "config.hpp"
#include "kernel/Logger.hpp"
#include "kernel/Message.hpp"

MqttService::MqttService(NetworkConnectionService* networkService, const char* broker, int port,
                         const char* clientId)
    : mqttClient(espClient), 
      broker(broker), 
      port(port), 
      clientId(clientId)
{
    this->networkService = networkService;
}

void MqttService::init() { mqttClient.setServer(broker, port); }

void MqttService::connect()
{
    if (!this->networkService->isConnected())
    {
        this->connected = false;
        return;
    }

    if (!this->mqttClient.connected())
    {
        Logger.log(F("[MQTT] Connecting..."));
        if (this->mqttClient.connect(clientId))
        {
            Logger.log(F("[MQTT] Connected"));
            this->connected = true;
        }
        else
        {
            Logger.log(String("[MQTT] Failed: ") + String(this->mqttClient.state()));
            this->connected = false;
        }
    }
    else
    {
        this->connected = true;
    }
}

void MqttService::loop() { this->mqttClient.loop(); }

bool MqttService::send(Message* msg)
{
    if (!this->mqttClient.connected())
    {
        return false;
    }

    return this->mqttClient.publish(msg->topic, msg->payload);
}
