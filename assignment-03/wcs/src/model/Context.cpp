#include "Context.hpp"

#include <ArduinoJson.h>

Context::Context() {
  this->mode = UNCONNECTED;
  setValveOpening(0);
  this->buttonPressed = false;
}

void Context::onBtnPressed() { this->buttonPressed = true; }

void Context::serializeData(JsonDocument& doc) {
  doc["ch_mode"] = this->buttonPressed;

  if (this->potValue >= 0) {
    doc["pot"] = this->potValue;
  }

  // Reset button pressed state after serialization
  this->buttonPressed = false;
}

void Context::setValveOpening(unsigned int opening) {
  this->valveOpening = opening;
}

unsigned int Context::getValveOpening() { return this->valveOpening; }

const char* Context::getLCDMessage() const { return this->lcdMessage; }

void Context::setLCDMessage(const char* msg) { this->lcdMessage = msg; }
