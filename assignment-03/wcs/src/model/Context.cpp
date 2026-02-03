#include "Context.hpp"

#include <ArduinoJson.h>

#include "config.hpp"
#include "kernel/Logger.hpp"

// Command table definition
const Context::CmdEntry Context::cmdTable[] = {
    {"set_valve", &Context::cmdSetValve},
    {"set_mode", &Context::cmdSetMode},
};

Context::Context() {
  this->mode = UNCONNECTED;
  this->valveOpening = 0;
  this->potValue = 0.0;
  this->buttonPressed = false;
  this->lcdMessage = LCD_UNCONNECTED;

  // Initialize command buffers
  this->valveCmd.pending = false;
  this->valveCmd.position = 0;
  this->valveCmd.timestamp = 0;

  this->modeCmd.pending = false;
  this->modeCmd.mode = UNCONNECTED;
  this->modeCmd.timestamp = 0;
}

// ============ Command Handlers ============

void Context::cmdSetValve(JsonDocument& doc) {
  if (doc.containsKey("value")) {
    unsigned int pos = doc["value"];
    if (pos <= 100) {  // Validate range
      valveCmd.pending = true;
      valveCmd.position = pos;
      valveCmd.timestamp = millis();
      Logger.log(F("CMD_VALVE_OK"));
    } else {
      Logger.log(F("CMD_VALVE_RANGE"));
    }
  }
}

void Context::cmdSetMode(JsonDocument& doc) {
  if (doc.containsKey("value")) {
    const char* modeStr = doc["value"];
    Mode newMode;

    if (strcmp(modeStr, "AUTOMATIC") == 0) {
      newMode = AUTOMATIC;
    } else if (strcmp(modeStr, "MANUAL") == 0) {
      newMode = MANUAL;
    } else if (strcmp(modeStr, "UNCONNECTED") == 0) {
      newMode = UNCONNECTED;
    } else {
      Logger.log(F("CMD_MODE_INVALID"));
      return;
    }

    modeCmd.pending = true;
    modeCmd.mode = newMode;
    modeCmd.timestamp = millis();
    Logger.log(F("CMD_MODE_OK"));
  }
}

// ============ Command Consumption ============

bool Context::hasValveCommand() { return valveCmd.pending; }

unsigned int Context::consumeValveCommand() {
  valveCmd.pending = false;
  return valveCmd.position;
}

bool Context::hasModeCommand() { return modeCmd.pending; }

Context::Mode Context::consumeModeCommand() {
  modeCmd.pending = false;
  return modeCmd.mode;
}

// ============ State Getters ============

Context::Mode Context::getMode() const { return mode; }

unsigned int Context::getValveOpening() const { return valveOpening; }

bool Context::wasButtonPressed() {
  bool pressed = buttonPressed;
  buttonPressed = false;  // Reset after read
  return pressed;
}

float Context::getPotValue() const { return potValue; }

const char* Context::getLCDMessage() const { return lcdMessage; }

// ============ State Setters ============

void Context::setValveOpening(unsigned int opening) {
  this->valveOpening = opening;
}

void Context::setPotValue(float value) { this->potValue = value; }

void Context::setButtonPressed() { this->buttonPressed = true; }

void Context::setLCDMessage(const char* msg) { this->lcdMessage = msg; }

void Context::setMode(Mode mode) { this->mode = mode; }

// ============ Command Registry ============

const Context::CmdEntry* Context::getCmdTable() { return cmdTable; }

int Context::getCmdTableSize() { return sizeof(cmdTable) / sizeof(CmdEntry); }
