#ifndef __HWPLATFORM_HPP__
#define __HWPLATFORM_HPP__

#include <devices/Led.hpp>
#include <devices/Sonar.hpp>

class HWPlatform {
 private:
  Led* greenLed;
  Led* redLed;
  Sonar* sonar;

 public:
  /**
   * @brief Construct a new HWPlatform object
   *
   */
  HWPlatform();

  /**
   * @brief Test the hardware
   *
   */
  void test();

  /**
   * @brief Get the Sonar
   *
   * @return Sonar* The sonar
   */
  Sonar* getSonar();

  /**
   * @brief Get the Red Led
   *
   * @return Led* The red Led
   */
  Led* getRedLed();

  /**
   * @brief Get the Green Led
   *
   * @return Led* The green Led
   */
  Led* getGreenLed();
};

#endif  // __HWPLATFORM_HPP__