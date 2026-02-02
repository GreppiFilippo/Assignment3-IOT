#ifndef __BUTTON__
#define __BUTTON__

/**
 * @brief Abstract base class representing a button device.
 *
 */
class Button
{
   public:
    /**
     * @brief Check if the button is currently pressed.
     *
     * @return true if the button is pressed
     * @return false if the button is not pressed
     */
    virtual bool isPressed() = 0;
};

#endif
