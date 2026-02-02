#include "kernel/MsgService.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

class ConnectionTask : public Task {
 private:
  Context* pContext;
  MsgServiceClass* pMsgService;

  enum State {
    UNCONNECTED,
    CONNECTED,
  } state;

  unsigned long stateTimestamp;
  bool justEntered;

  void receive();
  void send();

 public:
  ConnectionTask(Context* context, MsgServiceClass* msgService);
  void tick() override;

 private:
  void setState(State s);
  long elapsedTimeInState();
  bool checkAndSetJustEntered();
  bool isConnected();
};