#include "Context.hpp"

#include <config.hpp>
#include <kernel/Logger.hpp>
#include <kernel/Message.hpp>

Context::Context()
{
    this->waterLevel = 0.0f;
    this->messageCount = 0;
}

void Context::setWaterLevel(float level, unsigned long timestamp)
{
    this->waterLevel = level;

    // Costruzione JSON
    char payload[PAYLOAD_SIZE];
    snprintf(payload, PAYLOAD_SIZE, "{\"level\":%.2f,\"timestamp\":%lu}", level, timestamp);

    addMessage(MQTT_TOPIC_LEVEL, payload);
}

float Context::getWaterLevel() const { return waterLevel; }

void Context::addMessage(const char* topic, const char* payload)
{
    if (messageCount >= MAX_PENDING_MESSAGES)
    {
        Logger.log(F("[Context] Message queue full! Dropping message."));
        return;
    }

    pendingMessages[messageCount].topic = topic;
    strncpy(pendingMessages[messageCount].payload, payload, PAYLOAD_SIZE - 1);
    pendingMessages[messageCount].payload[PAYLOAD_SIZE - 1] = '\0';
    messageCount++;
}

Message** Context::getMessages()
{
    static Message* messagePointers[MAX_PENDING_MESSAGES + 1];

    for (int i = 0; i < messageCount; i++)
    {
        messagePointers[i] = &pendingMessages[i];
    }
    messagePointers[messageCount] = nullptr;

    return messagePointers;
}

void Context::clearMessages() { messageCount = 0; }

int Context::getMessageCount() const { return messageCount; }
