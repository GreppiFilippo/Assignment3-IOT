#ifndef __PROXIMITYSENSOR__
#define __PROXIMITYSENSOR__

/**
 * @brief Abstract base class for proximity sensors.
 *
 */
class ProximitySensor
{
   public:
    /**
     * Get the distance measured by the proximity sensor.
     *
     * @return float representing the distance in appropriate units
     */
    virtual float getDistance() = 0;
};

#endif
