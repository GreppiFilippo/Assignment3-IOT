#ifndef __HWPLATFORM__
#define __HWPLATFORM__

#include "devices/Button.hpp"
#include "devices/LCD.hpp"
#include "devices/Potentiometer.hpp"
#include "devices/ServoMotor.hpp"

/**
 * @brief Hardware Platform abstraction class
 *
 */
class HWPlatform {
 private:
  ServoMotor* pServo;
  Potentiometer* pPotentiometer;
  LCD* pLCD;
  Button* pButton;

 public:
  HWPlatform();
  void init();
  void test();

  ServoMotor* getServoMotor();
  Potentiometer* getPotentiometer();
  LCD* getLCD();
  Button* getButton();
};

#endif  // __HWPLATFORM__