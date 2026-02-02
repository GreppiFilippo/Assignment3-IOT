#include "HWPlatform.hpp"

#include "config.hpp"
#include "devices/ButtonImpl.hpp"
#include "devices/ServoMotorImpl.hpp"

HWPlatform::HWPlatform() {
  this->pServo = new ServoMotorImpl(SERVO_PIN);
  this->pPotentiometer = new Potentiometer(POT_PIN);
  this->pLCD = new LCD(LCD_ADDR, LCD_COLS, LCD_ROWS);
  this->pButton = new ButtonImpl(BUTTON_PIN);
}

void HWPlatform::init() {
  this->pServo->on();
  this->pPotentiometer->sync();
  this->pLCD->clear();
}

ServoMotor* HWPlatform::getServoMotor() { return this->pServo; }

Potentiometer* HWPlatform::getPotentiometer() { return this->pPotentiometer; }

LCD* HWPlatform::getLCD() { return this->pLCD; }

Button* HWPlatform::getButton() { return this->pButton; }

void HWPlatform::test() {}
