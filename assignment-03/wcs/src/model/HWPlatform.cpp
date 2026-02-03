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

void HWPlatform::test() {
  this->pLCD->print("Testing Servo Motor...", MODE_LINE);
  this->pServo->on();
  delay(1000);
  this->pServo->setPosition(0);
  delay(1000);
  this->pServo->setPosition(90);
  delay(1000);
  this->pServo->setPosition(180);
  delay(1000);
  this->pServo->off();
  this->pLCD->clear();

  this->pLCD->print("Testing Potentiometer...", MODE_LINE);
  this->pPotentiometer->sync();
  float potValue = this->pPotentiometer->getValue();
  this->pLCD->print(("Value: " + String(potValue)).c_str(), MODE_LINE);
  delay(2000);
  this->pLCD->clear();
  this->pLCD->print("Testing Button...", MODE_LINE);
  while (!this->pButton->wasPressed()) {
    // Wait for button press
  }
  this->pLCD->print("Button Pressed!", MODE_LINE);
  delay(2000);
  this->pLCD->clear();
}
