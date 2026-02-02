#include "devices/Button.hpp"
#include "devices/LCD.hpp"
#include "devices/Potentiometer.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class SystemTask : public Task {
 private:
  Context* pContext;
  LCD* pLCD;
  Button* pBtn;
  Potentiometer* pPot;

  enum State { EVALUATING, AUTOMATIC, MANUAL } state;

  bool justEntered;
  unsigned long stateTimestamp;

 public:
  SystemTask(Context* context, LCD* lcd, Button* btn, Potentiometer* pot);
  void tick() override;
  void setState(State s);

 private:
  long elapsedTimeInState();
  bool checkAndSetJustEntered();
};