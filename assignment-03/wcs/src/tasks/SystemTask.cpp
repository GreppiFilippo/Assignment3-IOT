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
    case UNCONNECTED:
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_UNCONNECTED);
      }

      pContext->setValveOpening(pPot->getValue());

      if (this->pContext->getMsgMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      } else if (this->pContext->getMsgMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }
      break;
    case AUTOMATIC:
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_AUTOMATIC_MODE);
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->onBtnPressed();
      }

      this->pContext->setValveOpening(pContext->getMsgOpening());

      if (this->pContext->getMsgMode() == Context::UNCONNECTED) {
        this->setState(UNCONNECTED);
      } else if (this->pContext->getMsgMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }

      break;
    case MANUAL:

      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_MANUAL_MODE);
      }

      this->pPot->sync();
      float potValue = this->pPot->getValue();
      this->pContext->setValveOpening(pContext->getMsgOpening());

      if (this->pBtn->wasPressed()) {
        this->pContext->setButtonPressed();
      }

      if (this->pContext->getMsgMode() == Context::UNCONNECTED) {
        this->setState(UNCONNECTED);
      } else if (this->pContext->getMsgMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      }

      break;
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
