#include "tasks/LCDTask.hpp"

#include "config.hpp"

LCDTask::LCDTask(LCD* lcd, Context* pContext) {
  this->lcd = lcd;
  this->pContext = pContext;
  this->lastMsg[0] = '\0';  // Initialize lastMsg as empty string
}

void LCDTask::tick() {
  const char* msg = this->pContext->getLCDMessage();
  float valvePos = this->pContext->getValveOpening();
  char buf[20];
  snprintf(buf, sizeof(buf), "Valve: %.1f%%", valvePos);
  if (strcmp(msg, this->lastMsg) != 0) {
    this->lcd->print(msg, MODE_LINE);
    this->lcd->print(buf, VALVE_LINE);
    strncpy(this->lastMsg, msg, sizeof(this->lastMsg) - 1);
    this->lastMsg[sizeof(this->lastMsg) - 1] = '\0';
  }
}
