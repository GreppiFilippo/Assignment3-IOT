#include "SystemTask.hpp"

#include "config.hpp"
#include "kernel/Logger.hpp"

SystemTask::SystemTask(Context* context, Button* btn, Potentiometer* pot) {
  this->pContext = context;
  this->pBtn = btn;
  this->pPot = pot;
  this->setState(UNCONNECTED);
  this->lastButtonPressTimestamp = 0;
}

void SystemTask::tick() {
  // ========== Read local inputs (always) ==========
  this->pContext->setButtonPressed(this->pBtn->wasPressed());

  // Record timestamp when button is pressed
  if (this->pContext->consumeButtonPressed()) {
    this->lastButtonPressTimestamp = millis();
  }

  // Set btn nested object: { val: true|false, who: "wcs" }
  unsigned long lastMsgSent = this->pContext->getLastMsgSentTimestamp();
  JsonObject btnObj = this->pContext->getOrCreateNestedObject(BUTTON_PRESSED_JSON);
  btnObj["val"] = this->lastButtonPressTimestamp > lastMsgSent;
  btnObj["who"] = "wcs";

  this->pPot->sync();
  float potValue = this->pPot->getValue();
  this->pContext->setField(POTENTIOMETER_JSON, static_cast<int>(potValue));

  switch (this->state) {
    case UNCONNECTED: {
      if (this->checkAndSetJustEntered()) {
        Logger.log(F("[ST] UNCONNECTED"));
        this->pContext->setLCDLine(MODE_LINE, LCD_UNCONNECTED);
      }

      if (isModeCommandAvailable()) {
        const char* mode = getModeCommandValue();
        if (strcmp(mode, MODE_AUTOMATIC) == 0) {
          this->pContext->setLCDLine(MODE_LINE, LCD_AUTOMATIC_MODE);
          setState(CONNECTED);
          break;
        } else if (strcmp(mode, MODE_MANUAL) == 0) {
          this->pContext->setLCDLine(MODE_LINE, LCD_MANUAL_MODE);
          setState(CONNECTED);
          break;
        }
      }
      /*
       * In UNCONNECTED state, the valve position is directly controlled by
       * the potentiometer.
       */
      this->pContext->setReceivedValvePosition(
          static_cast<unsigned int>(potValue));
    } break;
    case CONNECTED: {
      if (this->checkAndSetJustEntered()) {
        Logger.log(F("[ST] CONNECTED"));
      }

      unsigned long lastMsg =
          this->pContext->getLastValidReceivedMsgTimestamp();
      if (lastMsg > 0 && (millis() - lastMsg >= TIMEOUT_UNCONNECTED)) {
        setState(UNCONNECTED);
        break;
      }

      if (isModeCommandAvailable()) {
        const char* mode = getModeCommandValue();
        if (strcmp(mode, MODE_UNCONNECTED) == 0) {
          setState(UNCONNECTED);
          break;
        }
      }
      /*
       * In CONNECTED state, the valve position is controlled by commands
       */
      if (isValveCommandAvailable()) {
        auto position = this->getValveCommandValue();
        this->pContext->setReceivedValvePosition(position);
      }

    } break;
  }

  // ========== Update valve on display ==========
  {
    struct LocalCStr {
      char buf[20];
      const char* c_str() const { return buf; }
    } valStr;
    int val = static_cast<int>(this->pContext->getReceivedValvePosition());
    snprintf(valStr.buf, sizeof(valStr.buf), "Valve: %d%%", val);
    this->pContext->setLCDLine(VALVE_LINE, valStr.c_str());
  }
}

bool SystemTask::isModeCommandAvailable() {
  StaticJsonDocument<INPUT_JSON_SIZE>& json = this->pContext->getReceivedJson();
  return json.containsKey(MODE_COMMAND_JSON);
}

const char* SystemTask::getModeCommandValue() {
  StaticJsonDocument<INPUT_JSON_SIZE>& json = this->pContext->getReceivedJson();
  return json[MODE_COMMAND_JSON];
}

bool SystemTask::isValveCommandAvailable() {
  StaticJsonDocument<INPUT_JSON_SIZE>& json = this->pContext->getReceivedJson();
  return json.containsKey(VALVE_COMMAND_JSON);
}

unsigned int SystemTask::getValveCommandValue() {
  StaticJsonDocument<INPUT_JSON_SIZE>& json = this->pContext->getReceivedJson();
  return json[VALVE_COMMAND_JSON];
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
