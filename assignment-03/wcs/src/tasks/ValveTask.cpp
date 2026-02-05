#include "ValveTask.hpp"

#include <kernel/Logger.hpp>

#include "config.hpp"

ValveTask::ValveTask(Context* context, ServoMotor* servo)
    : Task(), pContext(context), pServo(servo) {
  this->currentPosition = 0;
  this->targetPositionVal = 0;
  this->moveDuration = 0;
  this->setState(IDLE);
}

void ValveTask::tick() {
  switch (this->state) {
    case IDLE:

      if (this->checkAndSetJustEntered()) {
        Logger.log(F("[VT] IDLE"));
        this->pServo->off();
      }

      if (this->pContext->getReceivedValvePosition() != this->currentPosition) {
        this->targetPositionVal = this->pContext->getReceivedValvePosition();
        this->pServo->setPosition(mapValvePosition(this->targetPositionVal));
        this->moveDuration =
            abs(this->targetPositionVal - this->currentPosition) *
            MSEC_PER_PERCENT;

        this->setState(MOVING);
      }
      break;

    case MOVING:
      if (this->checkAndSetJustEntered()) {
        Logger.log(F("[VT] MOVING"));
        this->pServo->on();
      }

      if (this->elapsedTimeInState() >= this->moveDuration) {
        this->currentPosition = this->targetPositionVal;
        this->setState(IDLE);
      }
      break;
  }
}

uint8_t ValveTask::mapValvePosition(uint8_t position) {
  return map(position, 0, 100, VALVE_MIN_ANGLE, VALVE_MAX_ANGLE);
}

bool ValveTask::checkAndSetJustEntered() {
  bool bak = justEntered;
  if (justEntered) {
    justEntered = false;
  }
  return bak;
}

void ValveTask::setState(State s) {
  state = s;
  stateTimestamp = millis();
  justEntered = true;
}

unsigned long ValveTask::elapsedTimeInState() {
  return millis() - stateTimestamp;
}
