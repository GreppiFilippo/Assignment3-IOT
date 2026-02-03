#include "devices/ServoMotor.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class ValveTask : public Task {
 private:
  Context* pContext;
  ServoMotor* pServo;
  unsigned int currentPosition;

  long stateTimestamp;
  bool justEntered;

  enum State {
    IDLE,
    MOVING,
  } state;

  void moveValve(int position);
  bool inPosition();
  void setState(State s);
  bool checkAndSetJustEntered();
  long elapsedTimeInState();

 public:
  ValveTask(Context* context, ServoMotor* servo);
  void tick() override;
};