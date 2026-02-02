#ifndef __BUTTONIMPL__
#define __BUTTONIMPL__

#include "Button.hpp"

#define DEBOUNCE_DELAY 50

/**
 * @brief Implementation of a button device with debouncing.
 *
 */
class ButtonImpl : public Button {
 public:
  ButtonImpl(int pin);
  bool isPressed() override;
  bool wasPressed() override;

 private:
  int pin;
  bool lastState;
  bool currentState;
  bool previousStableState;
  unsigned long lastDebounceTime;
};

#endif
