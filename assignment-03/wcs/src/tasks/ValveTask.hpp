#include "devices/ServoMotor.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class ValveTask : public Task {
 private:
  Context* pContext;
  ServoMotor* pServo;

  enum State {
    IDLE,
    ADJUSTING,
  };

  void adjustValve();
  bool inPosition();

 public:
  ValveTask(Context* context, ServoMotor* servo);
  void tick() override;
};