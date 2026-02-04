#include "SystemTask.hpp"

#include "config.hpp"

static int getMappedPotValue(float potValue) { return (int)potValue; }

SystemTask::SystemTask(Context* context, Button* btn, Potentiometer* pot) {
  this->pContext = context;
  this->pBtn = btn;
  this->pPot = pot;
  this->setState(UNCONNECTED);
}

void SystemTask::tick() {
  // Update valve position on LCD
  char buf[20];
  unsigned int valvePos = this->pContext->getValveTargetPosition();
  snprintf(buf, sizeof(buf), "Valve: %d%%", valvePos);
  this->pContext->setLCDLine(VALVE_LINE, buf);

  switch (this->state) {
    case UNCONNECTED: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDLine(MODE_LINE, LCD_UNCONNECTED);
        this->pContext->setMode(Context::UNCONNECTED);
      }
      /*
       * Handle direct valeve opening through potentiometer in unconnected mode
       */
      this->pPot->sync();
      float potValue = this->pPot->getValue();
      this->pContext->setRequestedValveOpening(getMappedPotValue(potValue));

      if (this->pContext->hasModeCommand()) {
        Context::Mode newMode = this->pContext->consumeModeCommand();
        if (newMode == Context::MANUAL) {
          setState(MANUAL);
          break;
        } else if (newMode == Context::AUTOMATIC) {
          setState(AUTOMATIC);
          break;
        }
      }
    } break;

    case AUTOMATIC: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDLine(MODE_LINE, LCD_AUTOMATIC_MODE);
        this->pContext->setMode(Context::AUTOMATIC);
      }

      if (millis() - this->pContext->getLastValidMsgTimestamp() >
          TIMEOUT_UNCONNECTED) {
        setState(UNCONNECTED);
        return;
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->setButtonPressed();
      }

      if (this->pContext->hasModeCommand()) {
        Context::Mode newMode = this->pContext->consumeModeCommand();
        if (newMode == Context::MANUAL) {
          setState(MANUAL);
          return;
        } else if (newMode == Context::UNCONNECTED) {
          setState(UNCONNECTED);
          return;
        }
      }

      if (this->pContext->hasValveCommand()) {
        unsigned int valvePos = this->pContext->consumeValveCommand();
        this->pContext->setRequestedValveOpening(valvePos);
      }
    } break;

    case MANUAL: {
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDLine(MODE_LINE, LCD_MANUAL_MODE);
        this->pContext->setMode(Context::MANUAL);
      }

      if (millis() - this->pContext->getLastValidMsgTimestamp() >
          TIMEOUT_UNCONNECTED) {
        setState(UNCONNECTED);
        return;
      }

      if (this->pContext->hasModeCommand()) {
        Context::Mode newMode = this->pContext->consumeModeCommand();
        if (newMode == Context::AUTOMATIC) {
          setState(AUTOMATIC);
          return;
        } else if (newMode == Context::UNCONNECTED) {
          setState(UNCONNECTED);
          return;
        }
      }

      if (this->pBtn->wasPressed()) {
        this->pContext->setButtonPressed();
      }

      if (this->pContext->hasValveCommand()) {
        unsigned int valvePos = this->pContext->consumeValveCommand();
        this->pContext->setRequestedValveOpening(valvePos);
      }
      /*
       * Handle potentiometer value changes in manual mode: data are prepared to
       * be sent to remote cus
       */
      this->pPot->sync();
      float potValue = this->pPot->getValue();
      this->pContext->setPotValueToValidate(getMappedPotValue(potValue));
    } break;
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
