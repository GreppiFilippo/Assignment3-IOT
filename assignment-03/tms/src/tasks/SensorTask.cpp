#include "SensorTask.hpp"
#include "kernel/Logger.hpp"

SensorTask::SensorTask(Context* context, ProximitySensor* sonar, int freq)
    : pContext(context), pSonar(sonar), frequency(freq), level(0.0f), state(IDLE) {
}

void SensorTask::tick() {
    switch (state) {
        case IDLE:
            // TODO: Handle IDLE state
            break;

        case READING_SENSOR:
            measure();
            break;

        default:
            break;
    }
}

void SensorTask::measure() {
    // TODO: Implement sensor measurement
    // This should read from the proximity sensor and update the context
}
