#include "NetworkTask.hpp"

#include <esp32-hal.h>

#include "config.hpp"
#include "kernel/Logger.hpp"

#define T (SAMPLING_INTERVAL_MS)

NetworkTask::NetworkTask(NetworkConnectionService* pNetworkService,
                         ProtocolService* pProtocolService, Light* pAliveLight, Light* pErrorLight,
                         Context* pContext)
{
    this->pNetworkService = pNetworkService;
    this->pProtocolService = pProtocolService;
    this->pAliveLight = pAliveLight;
    this->pErrorLight = pErrorLight;
    this->pContext = pContext;
    this->setState(CONNECTING);
}

void NetworkTask::init() { this->lastSentTime = 0; }

void NetworkTask::tick()
{
    // Always call protocol loop for keep-alive and message processing
    this->pProtocolService->loop();

    switch (this->state)
    {
        case CONNECTING:
            if (this->checkAndSetJustEntered())
            {
                Logger.log(F("[NT] CONNECTING"));
            }

            // Connect network layer first
            this->pNetworkService->connect();
            
            // Then connect protocol layer
            if (this->pNetworkService->isConnected())
            {
                this->pProtocolService->connect();

                if (this->pProtocolService->isConnected())
                {
                    this->setState(NETWORK_OK);
                } else {
                    this->setState(NETWORK_ERROR);
                }
            } else {
                this->setState(NETWORK_ERROR);
            }
            break;
        case NETWORK_OK:
            if (this->checkAndSetJustEntered())
            {
                Logger.log(F("[NT] NETWORK_OK"));
                this->pAliveLight->switchOn();
                this->pErrorLight->switchOff();
            }

            // Check both layers
            if (!this->pNetworkService->isConnected() || !this->pProtocolService->isConnected())
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
                Logger.log(F("[NT] NETWORK_ERROR"));

                this->pAliveLight->switchOff();
                this->pErrorLight->switchOn();
            }

            // Try to reconnect both layers
            this->pNetworkService->connect();

            if (this->pNetworkService->isConnected())
            {
                this->pProtocolService->connect();

                if (this->pProtocolService->isConnected())
                {
                    this->setState(NETWORK_OK);
                }
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
    if (!this->pProtocolService->isConnected())
    {
        return;
    }

    int msgCount = this->pContext->getMessageCount();
    if (msgCount == 0)
    {
        return;  // Nothing to send
    }

    Message** msgs = this->pContext->getMessages();
    int sentCount = 0;
    
    for (int i = 0; msgs[i] != nullptr; i++)
    {
        if (this->pProtocolService->send(msgs[i]))
        {
            Logger.log(String("[NT] Sent message: topic=") + String(msgs[i]->topic) + 
                      String(" payload=") + String(msgs[i]->payload));
            sentCount++;
        }
        else
        {
            Logger.log(String("[NT] Failed to send message: topic=") + String(msgs[i]->topic));
        }
    }

    // Clear sent messages
    if (sentCount > 0)
    {
        this->pContext->clearMessages();
        Logger.log(String("[NT] Cleared ") + String(sentCount) + String(" messages"));
    }
}
