#ifndef __SENSOR_TASK_HPP__
#define __SENSOR_TASK_HPP__

#include "model/Context.hpp"
#include "devices/ProximitySensor.hpp"
#include "kernel/Task.hpp"

class SensorTask : public Task
{
private:
    Context* pContext;
    ProximitySensor* pSonar;
    float level;
    int frequency;

    enum State
    {
        IDLE,
        READING_SENSOR
    } state;
    void measure();
public:
    SensorTask(Context* context, ProximitySensor* sonar, int freq);
    void tick() override;
};

#endif // __SENSOR_TASK_HPP__
