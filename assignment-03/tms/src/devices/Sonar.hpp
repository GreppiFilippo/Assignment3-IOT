#ifndef __SONAR__
#define __SONAR__

#include "ProximitySensor.hpp"

#define NO_OBJ_DETECTED -1

/**
 * @brief Class representing a sonar proximity sensor.
 *
 */
class Sonar : public ProximitySensor {
 public:
  Sonar(int echoPin, int trigPin, long maxTime);
  float getDistance() override;
  void setTemperature(float temp);

 private:
  const float vs = 331.5 + 0.6 * 20;
  float getSoundSpeed();

  float temperature;
  int echoPin, trigPin;
  long timeOut;
};

#endif
