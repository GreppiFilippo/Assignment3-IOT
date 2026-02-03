#include "Context.hpp"

Context::Context() {
  this->mode = UNCONNECTED;
  setValveOpening(0);
  this->buttonPressed = false;
}

void Context::setButtonPressed() {
  // Implementation for handling button press
}

void Context::setValveOpening(unsigned int opening) {
  this->valveOpening = opening;
}

unsigned int Context::getValveOpening() { return this->valveOpening; }

const char* Context::getLCDMessage() const { return this->lcdMessage; }

void Context::setLCDMessage(const char* msg) { this->lcdMessage = msg; }
