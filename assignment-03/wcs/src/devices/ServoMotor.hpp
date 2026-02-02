#ifndef __SERVO_MOTOR__
#define __SERVO_MOTOR__

/**
 * @brief Abstract base class representing a servo motor.
 *
 */
class ServoMotor
{
   public:
    /**
     * @brief Turn the servo motor on.
     *
     */
    virtual void on() = 0;

    /**
     * @brief Check if the servo motor is on.
     *
     * @return true if on
     * @return false if off
     */
    virtual bool isOn() = 0;

    /**
     * @brief Set the position of the servo motor.
     *
     * @param angle Angle to set the servo to.
     */
    virtual void setPosition(int angle) = 0;

    /**
     * @brief Turn the servo motor off.
     *
     */
    virtual void off() = 0;
};

#endif
