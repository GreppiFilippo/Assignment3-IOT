#ifndef VALVE_TASK_HPP
#define VALVE_TASK_HPP

#include <Arduino.h>

#include "devices/ServoMotor.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

/**
 * @brief Task to control the valve position using a servo motor.
 *
 */
class ValveTask : public Task {
 public:
  ValveTask(Context* context, ServoMotor* servo);
  void tick() override;

 private:
  Context* pContext;
  ServoMotor* pServo;

  uint8_t currentPosition;
  uint8_t targetPositionVal;
  unsigned long moveDuration;
  unsigned long stateTimestamp;
  bool justEntered;

  enum State { IDLE, MOVING } state;

  /**
   * @brief Set the current state of the valve task.
   *
   * @param s New state to set.
   */
  void setState(State s);

  /**
   * @brief Check if just entered the current state.
   *
   * @return true if just entered
   * @return false otherwise
   */
  bool checkAndSetJustEntered();

  /**
   * @brief Get elapsed time in the current state.
   *
   * @return unsigned long Elapsed time in milliseconds.
   */
  unsigned long elapsedTimeInState();

  /**
   * @brief Map valve position percentage to servo angle.
   *
   * @param position Position in percentage (0-100)
   * @return uint8_t Mapped servo angle (0-90)
   */
  uint8_t mapValvePosition(uint8_t position);
};

#endif