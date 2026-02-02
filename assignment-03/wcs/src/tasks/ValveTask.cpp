#include "tasks/ValveTask.hpp"

#include <Arduino.h>

#include "config.hpp"

ValveTask::ValveTask(Context* context, ServoMotor* servo)
    : Task(), pContext(context), pServo(servo) {
  this->pServo->on();
}

void ValveTask::tick() {
  switch (this->state) {
    case IDLE:
      if (currentPosition != pContext->getValveOpening()) {
        setState(MOVING);
      }
      break;
    case MOVING:
      if (checkAndSetJustEntered()) {
        moveValve(pContext->getValveOpening());
      }
      if (inPosition()) {
        setState(IDLE);
      }
      break;
  }
}

void ValveTask::moveValve(int position) { this->pServo->setPosition(position); }

bool ValveTask::inPosition() {
  unsigned int time =
      (currentPosition - pContext->getValveOpening()) * MSEC_PER_PERCENT;
  return elapsedTimeInState() >= abs(time);
}

long ValveTask::elapsedTimeInState() { return millis() - this->stateTimestamp; }

void ValveTask::setState(State s) {
  state = s;
  stateTimestamp = millis();
  justEntered = true;
}

bool ValveTask::checkAndSetJustEntered() {
  bool bak = justEntered;
  if (justEntered) {
    justEntered = false;
  }
  return bak;
}
