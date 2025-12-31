#include "Led.hpp"

#include <esp32-hal.h>

Led::Led(int pin) {
  this->pin = pin;
  pinMode(pin, OUTPUT);
}

void Led::switchOn() { digitalWrite(pin, HIGH); }

void Led::switchOff() { digitalWrite(pin, LOW); };
