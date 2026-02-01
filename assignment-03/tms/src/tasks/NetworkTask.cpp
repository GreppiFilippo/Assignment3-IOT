#include "NetworkTask.hpp"

#include <ArduinoJson.h>
#include <esp32-hal.h>

#include <kernel/Logger.hpp>

#include "config.hpp"

#define T (1 / SAMPLING_INTERVAL_MS)

NetworkTask::NetworkTask(ConnectionService* pConnectionService, Light* pAliveLight,
                         Light* pErrorLight, Context* pContext)
{
    this->pConnectionService = pConnectionService;
    this->pAliveLight = pAliveLight;
    this->pErrorLight = pErrorLight;
    this->pContext = pContext;
    this->setState(CONNECTING);
}

void NetworkTask::init() { this->lastSentTime = 0; }

void NetworkTask::tick()
{
    switch (this->state)
    {
        case CONNECTING:
            if (this->checkAndSetJustEntered())
            {
                Logger.log(F("[NT] CONNECTING\n"));
            }

            this->pConnectionService->connect();
            if (this->pConnectionService->isConnected())
            {
                this->setState(NETWORK_OK);
            }
            break;
        case NETWORK_OK:
            if (this->checkAndSetJustEntered())
            {
                Logger.log(F("[NT] NETWORK_OK\n"));

                this->pAliveLight->switchOn();
                this->pErrorLight->switchOff();
            }

            if (!this->pConnectionService->isConnected())  // lost connection
            {
                this->setState(NETWORK_ERROR);
            }

            if (millis() - this->lastSentTime >= T)
            {
                this->sendData();
                this->lastSentTime = millis();
            }
            break;
        case NETWORK_ERROR:
            if (this->checkAndSetJustEntered())
            {
                Logger.log(F("[NT] NETWORK_ERROR\n"));

                this->pAliveLight->switchOff();
                this->pErrorLight->switchOn();
            }

            this->pConnectionService->connect();

            if (this->pConnectionService->isConnected())
            {
                this->setState(NETWORK_OK);
            }
            break;
        default:
            break;
    }
}

void NetworkTask::setState(State newState)
{
    state = newState;
    stateTimestamp = millis();
    justEntered = true;
}

long NetworkTask::elapsedTimeInState() { return millis() - stateTimestamp; }

bool NetworkTask::checkAndSetJustEntered()
{
    bool bak = justEntered;
    if (justEntered)
        justEntered = false;
    return bak;
}

void NetworkTask::sendData()
{
    // TODO: implement data sending logic using pConnectionService and pContext
    StaticJsonDocument<SENDING_BUFFER_SIZE> doc;
    // Populate the JSON document with data from pContext
    // Serialize JSON to string and send it via pConnectionService
    this->pContext->populateJsonDocument(doc);
    char buffer[SENDING_BUFFER_SIZE];
    size_t n = serializeJson(doc, buffer, sizeof(buffer));
    if (n > 0)
    {
        this->pConnectionService->send(buffer, n);
    }
    else
    {
        Logger.log(F("[NT] Error sending data\n"));
    }
}
