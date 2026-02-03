#include "tasks/ValveTask.hpp"

#include <Arduino.h>

#include "config.hpp"

ValveTask::ValveTask(Context* context, ServoMotor* servo)
    : Task(), pContext(context), pServo(servo) {
  this->pServo->on();
  this->currentPosition = 0;
  this->state = IDLE;
  this->stateTimestamp = millis();
  this->justEntered = true;
}

void ValveTask::tick() {
  switch (this->state) {
    case IDLE:
      if (this->pContext->getValveOpening() != currentPosition) {
        setState(MOVING);
      }
      break;

    case MOVING:
      if (checkAndSetJustEntered()) {
        moveValve(pContext->getValveOpening());
      }

      if (inPosition()) {
        currentPosition = pContext->getValveOpening();
        setState(IDLE);
      }
      break;
  }
}

void ValveTask::moveValve(int position) {
  // Map percentage (0-100) to servo angle
  int angle = map(position, 0, 100, VALVE_MIN_ANGLE, VALVE_MAX_ANGLE);
  this->pServo->setPosition(angle);
}

bool ValveTask::inPosition() {
  unsigned int time =
      abs((int)(currentPosition - pContext->getValveOpening())) *
      MSEC_PER_PERCENT;
  return elapsedTimeInState() >= time;
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
