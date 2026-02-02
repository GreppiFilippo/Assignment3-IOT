#ifndef __HWPLATFORM_HPP__
#define __HWPLATFORM_HPP__

#include <devices/Light.hpp>
#include <devices/ProximitySensor.hpp>

class HWPlatform
{
   private:
    Light* aliveLight;
    Light* errorLight;
    ProximitySensor* proximitySensor;

   public:
    /**
     * @brief Construct a new HWPlatform object
     *
     */
    HWPlatform();

    /**
     * @brief Initialize the hardware platform
     *
     */
    void init();

    /**
     * @brief Test the hardware
     *
     */
    void test();

    /**
     * @brief Get the Proximity Sensor
     *
     * @return The proximity sensor
     */
    ProximitySensor* getProximitySensor();

    /**
     * @brief Get the Alive Light object
     *
     * @return The alive light
     */
    Light* getAliveLight();

    /**
     * @brief Get the Error Light object
     *
     * @return The error light
     */
    Light* getErrorLight();
};

#endif  // __HWPLATFORM_HPP__