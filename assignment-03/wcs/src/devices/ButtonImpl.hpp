#ifndef __BUTTONIMPL__
#define __BUTTONIMPL__

#include "Button.hpp"

/**
 * @brief Implementation of a button device.
 *
 */
class ButtonImpl : public Button
{
   public:
    ButtonImpl(int pin);
    bool isPressed() override;

   private:
    int pin;
};

#endif
