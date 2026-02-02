#include "SensorsTask.hpp"

#include "kernel/Logger.hpp"

SensorsTask::SensorsTask(Context* context, ProximitySensor* sonar)
    : pContext(context), pSonar(sonar), level(0.0f)
{
}

void SensorsTask::tick() { measureLevel(); }

void SensorsTask::measureLevel()
{
    level = pSonar->getDistance();
    pContext->setWaterLevel(level, millis());
}
