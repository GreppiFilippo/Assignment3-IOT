#include "Context.hpp"

#include <ArduinoJson.h>

Context::Context() {
  this->mode = UNCONNECTED;
  setRequestedValveOpening(0);
  this->isModeChangeRequested = false;
}

void Context::setRequestedValveOpening(int opening) {
  this->valveOpening = opening;
}

void Context::setMode(Mode mode) { this->mode = mode; }

void Context::serializeData(JsonDocument& doc) {
  doc["ch_mode"] = this->isModeChangeRequested;

  if (this->potValue >= 0) {
    doc["pot"] = this->potValue;
  }

  // Reset button pressed state after serialization
  this->isModeChangeRequested = false;
}

void Context::setPotValue(float value) { this->potValue = value; }

int Context::getRequestedValveOpening() { return this->valveOpening; }

void Context::requestModeChange() { this->isModeChangeRequested = true; }

const char* Context::getLCDMessage() const { return this->lcdMessage; }

void Context::setLCDMessage(const char* msg) { this->lcdMessage = msg; }
