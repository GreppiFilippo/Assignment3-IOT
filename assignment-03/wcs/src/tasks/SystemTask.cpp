#include "SystemTask.hpp"

#include "config.hpp"

SystemTask::SystemTask(Context* context, Button* btn, Potentiometer* pot) {
  this->pContext = context;
  this->pBtn = btn;
  this->pPot = pot;
  this->setState(UNCONNECTED);
}

void SystemTask::tick() {
  switch (this->state) {
    case UNCONNECTED: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_UNCONNECTED);
      }

      int potValue =
          map(this->pPot->getValue(), 0, 1, VALVE_MIN_ANGLE, VALVE_MAX_ANGLE);

      pContext->setRequestedValveOpening(potValue);

      if (this->pContext->getMsgMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      } else if (this->pContext->getMsgMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }
      break;
    }
    case AUTOMATIC: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_AUTOMATIC_MODE);
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->requestModeChange();
      }

      this->pContext->setRequestedValveOpening(pContext->getMsgOpening());

      if (this->pContext->getMsgMode() == Context::UNCONNECTED) {
        this->setState(UNCONNECTED);
      } else if (this->pContext->getMsgMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }

      break;
    }
    case MANUAL: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_MANUAL_MODE);
      }

      this->pPot->sync();
      int potValue =
          map(this->pPot->getValue(), 0, 1, VALVE_MIN_ANGLE, VALVE_MAX_ANGLE);
      this->pContext->setPotValue(potValue);

      // TODO: to be changed
      this->pContext->setRequestedValveOpening(pContext->getMsgOpening());

      if (this->pBtn->wasPressed()) {
        this->pContext->requestModeChange();
      }

      if (this->pContext->getMsgMode() == Context::UNCONNECTED) {
        this->setState(UNCONNECTED);
      } else if (this->pContext->getMsgMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      }

      break;
    }
  }
}

void SystemTask::setState(State s) {
  state = s;
  stateTimestamp = millis();
  justEntered = true;
}

bool SystemTask::checkAndSetJustEntered() {
  bool bak = justEntered;
  if (justEntered) {
    justEntered = false;
  }
  return bak;
}
