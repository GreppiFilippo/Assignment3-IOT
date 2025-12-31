#ifndef __LED__
#define __LED__

#include "Light.hpp"

/**
 * @brief Implementation of an LED device.
 *
 */
class Led : public Light {
 public:
  Led(int pin);
  void switchOn() override;
  void switchOff() override;

 protected:
  int pin;
};

#endif
