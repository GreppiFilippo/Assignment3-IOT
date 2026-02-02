#include "kernel/MsgService.hpp"
#include "model/Context.hpp"

class ConnectionTask : public Task {
 private:
  Context* pContext;
  MsgServiceClass* pMsgService;

  enum State {
    UNCONNECTED,
    CONNECTED,
  };

  void receive();
  void send();

 public:
  ConnectionTask(Context* context, MsgServiceClass* msgService);
  void tick() override;
};