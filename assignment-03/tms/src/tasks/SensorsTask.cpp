#include "SensorsTask.hpp"

#include "kernel/Logger.hpp"

SensorsTask::SensorsTask(Context* context, ProximitySensor* sonar)
    : pContext(context), pSonar(sonar), level(0.0f)
{
}

void SensorsTask::tick() { measureLevel(); }

void SensorsTask::measureLevel()
{
    Logger.log(F(("[ST] Measuring water level...")));
    level = pSonar->getDistance();
    pContext->setWaterLevel(level, millis());
}
