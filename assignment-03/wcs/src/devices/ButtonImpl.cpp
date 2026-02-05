#include "ButtonImpl.hpp"

#include "Arduino.h"

ButtonImpl::ButtonImpl(int pin) {
  this->pin = pin;
  pinMode(pin, INPUT);
  this->lastState = LOW;
  this->currentState = LOW;
  this->previousStableState = LOW;
  this->lastDebounceTime = 0;
}

bool ButtonImpl::isPressed() {
  bool reading = digitalRead(pin) == HIGH;

  if (reading != lastState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (reading != currentState) {
      previousStableState = currentState;
      currentState = reading;
    }
  }

  lastState = reading;
  return currentState;
}

bool ButtonImpl::wasPressed() {
  bool prevState = currentState;
  isPressed();  // Update state

  // Rising edge: previous was LOW, current is HIGH
  return !prevState && currentState;
}
