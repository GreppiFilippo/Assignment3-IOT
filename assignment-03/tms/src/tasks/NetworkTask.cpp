#include "NetworkTask.hpp"

#include <esp32-hal.h>

NetworkTask::NetworkTask(ConnectionService* pConnectionService, Light* pAliveLight,
                         Light* pErrorLight, Context* pContext)
{
    this->pConnectionService = pConnectionService;
    this->pAliveLight = pAliveLight;
    this->pErrorLight = pErrorLight;
    this->pContext = pContext;
    this->setState(CONNECTING);
}

void NetworkTask::init() {}

void NetworkTask::tick()
{
    switch (this->state)
    {
        case CONNECTING:
            this->pConnectionService->connect();
            if (this->pConnectionService->isConnected())
            {
                this->setState(NETWORK_OK);
            }
            break;
        case NETWORK_OK:
            if (this->checkAndSetJustEntered())
            {
                this->pAliveLight->switchOn();
                this->pErrorLight->switchOff();
            }
            /* code */
            break;
        case NETWORK_ERROR:
            /* code */
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