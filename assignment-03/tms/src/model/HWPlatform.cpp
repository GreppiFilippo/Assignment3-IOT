
#include "HWPlatform.hpp"

#include <esp32-hal.h>

#include "config.hpp"
#include "kernel/Logger.hpp"

HWPlatform::HWPlatform() {
  this->greenLed = new Led(LED_GREEN_PIN);
  this->redLed = new Led(LED_RED_PIN);
  this->sonar = new Sonar(SONAR_ECHO_PIN, SONAR_TRIG_PIN, SONAR_TIMEOUT_US);
}

void HWPlatform::test() {
  // Test LEDs
  this->greenLed->switchOn();
  this->redLed->switchOn();
  delay(500);
  this->greenLed->switchOff();
  this->redLed->switchOff();
  delay(500);

  // Test Sonar
  float distance = this->sonar->getDistance();
  Logger::instance().log("Sonar distance: ");
  char buffer[16];
  snprintf(buffer, sizeof(buffer), "%.2f", distance);
  Logger::instance().log(buffer);
  Logger::instance().log(" cm");

  this->sonar->setTemperature(25.0);
  distance = this->sonar->getDistance();
  Logger::instance().log("Sonar distance at 25C: ");
  snprintf(buffer, sizeof(buffer), "%.2f", distance);
  Logger::instance().log(buffer);
  Logger::instance().log(" cm");
}

Sonar* HWPlatform::getSonar() { return this->sonar; }

Led* HWPlatform::getRedLed() { return this->redLed; }

Led* HWPlatform::getGreenLed() { return this->greenLed; }