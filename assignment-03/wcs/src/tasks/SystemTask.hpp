#include "devices/Button.hpp"
#include "devices/LCD.hpp"
#include "devices/Potentiometer.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class SystemTask : public Task {
 private:
  Context* pContext;
  Button* pBtn;
  Potentiometer* pPot;

  enum State { EVALUATING, AUTOMATIC, MANUAL } state;

  bool justEntered;
  unsigned long stateTimestamp;

 public:
  SystemTask(Context* context, Button* btn, Potentiometer* pot);
  void tick() override;

 private:
  void setState(State s);
  bool checkAndSetJustEntered();
};
