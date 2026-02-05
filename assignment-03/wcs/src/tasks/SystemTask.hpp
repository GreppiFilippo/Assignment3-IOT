#ifndef __SYSTEM_TASK__
#define __SYSTEM_TASK__

#include "devices/Button.hpp"
#include "devices/Potentiometer.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

/**
 * @brief SystemTask manages:
 * - FSM: UNCONNECTED / CONNECTED based on received mode from CUS
 * - Reading local inputs (button, potentiometer)
 * - Updating LCD display
 * - Deciding valve target: potentiometer (UNCONNECTED) or CUS command
 * (CONNECTED)
 */
class SystemTask : public Task {
 private:
  Context* pContext;
  Button* pBtn;
  Potentiometer* pPot;

  enum State { UNCONNECTED, CONNECTED } state;
  bool justEntered;
  unsigned long stateTimestamp;
  unsigned long lastButtonPressTimestamp;

 public:
  SystemTask(Context* context, Button* btn, Potentiometer* pot);
  void tick() override;

 private:
  void setState(State s);
  bool checkAndSetJustEntered();
  bool isValveCommandAvailable();
  unsigned int getValveCommandValue();
  bool isModeCommandAvailable();
  const char* getModeCommandValue();
};

#endif
