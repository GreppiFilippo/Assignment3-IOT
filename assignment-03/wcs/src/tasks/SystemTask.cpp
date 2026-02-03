#include "SystemTask.hpp"

#include "config.hpp"

SystemTask::SystemTask(Context* context, Button* btn, Potentiometer* pot) {
  this->pContext = context;
  this->pBtn = btn;
  this->pPot = pot;
  this->setState(UNCONNECTED);
}

void SystemTask::tick() {
  // ======== SENSOR READING & EVENT GENERATION ========
  
  // Check button press and notify Context (MsgTask will send event)
  if (this->pBtn->wasPressed()) {
    this->pContext->setButtonPressed();
  }

  // Read potentiometer and update Context
  this->pPot->sync();
  float potValue = this->pPot->getValue();
  // Convert 0.0-1.0 float to 0-100 percentage
  int mappedPot = (int)(potValue * 100.0);
  this->pContext->setPotValue(mappedPot);

  // ======== COMMAND EXECUTION FROM CUS ========
  
  // Apply mode command if received from CUS
  if (this->pContext->hasModeCommand()) {
    Context::Mode newMode = this->pContext->consumeModeCommand();
    
    switch (newMode) {
      case Context::UNCONNECTED:
        setState(UNCONNECTED);
        break;
      case Context::AUTOMATIC:
        setState(AUTOMATIC);
        break;
      case Context::MANUAL:
        setState(MANUAL);
        break;
    }
  }

  // ======== STATE-SPECIFIC BEHAVIOR ========
  
  switch (this->state) {
    case UNCONNECTED:
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_UNCONNECTED);
        this->pContext->setMode(Context::UNCONNECTED);
      }
      break;

    case AUTOMATIC:
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_AUTOMATIC_MODE);
        this->pContext->setMode(Context::AUTOMATIC);
      }
      break;

    case MANUAL:
      if (this->checkAndSetJustEntered()) {
        this->pContext->setLCDMessage(LCD_MANUAL_MODE);
        this->pContext->setMode(Context::MANUAL);
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
