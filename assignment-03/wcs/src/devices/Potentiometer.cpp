#include "Potentiometer.hpp"

#include <Arduino.h>

Potentiometer::Potentiometer(int pin) { this->pin = pin; }

void Potentiometer::sync() {
  value = analogRead(pin);
  updateSyncTime(millis());
}

float Potentiometer::getValue() { return map(value, 0, 1023, 0, 100); }

void Potentiometer::updateSyncTime(long time) { lastTimeSync = time; }

long Potentiometer::getLastSyncTime() { return lastTimeSync; }
