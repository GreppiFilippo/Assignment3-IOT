#ifndef __LIGHT__
#define __LIGHT__

/**
 * @brief Abstract base class representing a light device.
 *
 */
class Light
{
   public:
    /**
     * @brief Switch the light on.
     *
     */
    virtual void switchOn() = 0;

    /**
     * @brief Switch the light off.
     *
     */
    virtual void switchOff() = 0;
};

#endif
