#include "model/Context.hpp"
#include "kernel/MsgService.hpp"

class ConnectionTask {
    private:
        Context* pContext;
        MsgServiceClass* pMsgService;
        
        enum State {
            UNCONNECTED,
            CONNECTED,
        };
        
        void receive();
        void send();
};