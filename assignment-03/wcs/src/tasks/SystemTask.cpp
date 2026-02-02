#include "SystemTask.hpp"

#include "config.hpp"

SystemTask::SystemTask(Context* context, LCD* lcd, Button* btn,
                       Potentiometer* pot) {
  this->pContext = context;
  this->pLCD = lcd;
  this->pBtn = btn;
  this->pPot = pot;
}

void SystemTask::tick() {
  switch (this->state) {
    case EVALUATING:
      if (this->pContext->getMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      } else if (this->pContext->getMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }
      break;
    case AUTOMATIC:
      if (this->checkAndSetJustEntered()) {
        this->pLCD->print(LCD_AUTOMATIC_MODE);
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->setButtonPressed();
      }

      if (!this->pContext->isConnected()) {
        this->setState(EVALUATING);
      }

      if (this->pContext->getMode() == Context::MANUAL) {
        this->setState(MANUAL);
      }

      break;
    case MANUAL:

      if (this->checkAndSetJustEntered()) {
        this->pLCD->print(LCD_MANUAL_MODE);
      }

      this->pPot->sync();
      float potValue = this->pPot->getValue();
      this->pContext->setValveOpening(potValue);

      if (this->pContext->getMode() == Context::AUTOMATIC) {
        this->setState(AUTOMATIC);
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->setButtonPressed();
      }
      break;
  }
}

void SystemTask::setState(State s) {
  state = s;
  stateTimestamp = millis();
  justEntered = true;
}

long SystemTask::elapsedTimeInState() { return millis() - stateTimestamp; }

bool SystemTask::checkAndSetJustEntered() {
  bool bak = justEntered;
  if (justEntered) {
    justEntered = false;
  }
  return bak;
}
