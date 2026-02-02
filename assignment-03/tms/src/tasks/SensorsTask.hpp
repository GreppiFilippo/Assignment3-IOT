#ifndef __SENSORS_TASK_HPP__
#define __SENSORS_TASK_HPP__

#include "devices/ProximitySensor.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class SensorsTask : public Task
{
   private:
    Context* pContext;
    ProximitySensor* pSonar;
    float level;

    bool justEntered;
    unsigned long stateTimestamp;

    void measureLevel();
    long elapsedTimeInState();
    bool checkAndSetJustEntered();

   public:
    SensorsTask(Context* context, ProximitySensor* sonar);
    void tick() override;
};

#endif  // __SENSORS_TASK_HPP__
