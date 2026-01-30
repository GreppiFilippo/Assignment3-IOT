
#include "HWPlatform.hpp"

#include <esp32-hal.h>

#include <devices/Led.hpp>
#include <devices/Sonar.hpp>

#include "config.hpp"
#include "kernel/Logger.hpp"

HWPlatform::HWPlatform() {
  this->aliveLight = new Led(LED_GREEN_PIN);
  this->errorLight = new Led(LED_RED_PIN);
  this->proximitySensor =
      new Sonar(SONAR_ECHO_PIN, SONAR_TRIG_PIN, SONAR_TIMEOUT_US);
}

ProximitySensor* HWPlatform::getProximitySensor() {
  return this->proximitySensor;
}

Light* HWPlatform::getAliveLight() { return this->aliveLight; }

Light* HWPlatform::getErrorLight() { return this->errorLight; }

void HWPlatform::test() {
  Logger.log(F("HWPlatform: Testing hardware..."));

  Logger.log(F("HWPlatform: Testing alive light..."));
  this->aliveLight->switchOn();
  delay(500);
  this->aliveLight->switchOff();
  delay(500);

  Logger.log(F("HWPlatform: Testing error light..."));
  this->errorLight->switchOn();
  delay(500);
  this->errorLight->switchOff();
  delay(500);

  Logger.log(F("HWPlatform: Testing proximity sensor..."));

  for (int i = 0; i < 5; i++) {
    float distance = this->proximitySensor->getDistance();
    Logger.log("HWPlatform: Proximity sensor reading " + String(i + 1) + ": " +
               String(distance));
    delay(500);
  }

  Logger.log(F("HWPlatform: Hardware test completed."));
}
