#ifndef __SERVO_MOTOR_IMPL__
#define __SERVO_MOTOR_IMPL__

#include <Arduino.h>

#include "ServoMotor.hpp"
#include "ServoTimer2.hpp"

/**
 * @brief Class representing a servo motor implementation.
 *
 */
class ServoMotorImpl : public ServoMotor
{
   public:
    ServoMotorImpl(int pin);

    void on() override;
    bool isOn() override;
    void setPosition(int angle) override;
    void off() override;

   private:
    int pin;
    bool _on;
    ServoTimer2 motor;
};

#endif
