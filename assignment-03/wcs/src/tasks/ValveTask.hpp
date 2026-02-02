#include "kernel/Task.hpp"
#include "model/Context.hpp"

class ValveTask : public Task {
    private:
        Context* pContext;

        enum State {
            IDLE,
            ADJUSTING,
        };

        void adjustValve();
        bool inPosition();
};