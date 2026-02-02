#include "kernel/Task.hpp"
#include "model/Context.hpp"
#include "devices/LCD.hpp"
#include "devices/Button.hpp"


class SystemTask : public Task {
    private: 
        Context* pContext;
        LCD* pLCD;
        Button* pBtn;

        enum State {
            EVALUATING,
            AUTOMATIC,
            MANUAL
        } state;

        bool justEntered;

    public:
        void tick() override;
        void setState(State s);
};