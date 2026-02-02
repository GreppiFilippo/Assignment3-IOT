#include "ConnectionTask.hpp"

#include "config.hpp"

ConnectionTask::ConnectionTask(Context* context, MsgServiceClass* msgService) {
  this->pContext = context;
  this->pMsgService = msgService;
  this->state = UNCONNECTED;
}

void ConnectionTask::tick() {
  switch (this->state) {
    case UNCONNECTED:
      if (checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_UNCONNECTED);
      }
      if (this->isConnected()) {
        this->state = CONNECTED;
        break;
      }
    case CONNECTED:
      if (!this->pContext->isConnected()) {
        this->state = UNCONNECTED;
        break;
      }

      this->receive();
      this->send();
      break;
    default:
      break;
  }
}

void ConnectionTask::setState(State s) {
  state = s;
  stateTimestamp = millis();
  justEntered = true;
}

long ConnectionTask::elapsedTimeInState() { return millis() - stateTimestamp; }

bool ConnectionTask::checkAndSetJustEntered() {
  bool bak = justEntered;
  if (justEntered) {
    justEntered = false;
  }
  return bak;
}
