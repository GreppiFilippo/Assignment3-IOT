#include "SystemTask.hpp"
#include "config.hpp"

void SystemTask::tick()
{
    switch (this->state)
    {
    case EVALUATING:
        if (pContext->getMode() == Context::AUTOMATIC) {
            setState(AUTOMATIC);
        } else if (pContext->getMode() == Context::MANUAL) {
            setState(MANUAL);
        }
        break;
    case AUTOMATIC:
        pLCD->print(LCD_AUTOMATIC_MODE);
        break;
    case MANUAL:
        pLCD->print(LCD_MANUAL_MODE);
        break;
    }
}

void SystemTask::setState(State s)
{
    state = s;
    justEntered = true;
}