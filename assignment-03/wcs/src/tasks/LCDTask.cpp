#include "tasks/LCDTask.hpp"

#include "config.hpp"

LCDTask::LCDTask(LCD* lcd, Context* pContext) {
  this->lcd = lcd;
  this->pContext = pContext;
  this->lastMsg[0] = '\0';  // Initialize lastMsg as empty string
}

void LCDTask::tick() {
  const char* msg = this->pContext->getLCDMessage();

  if (strcmp(msg, this->lastMsg) != 0) {
    this->lcd->print(msg);
    strncpy(this->lastMsg, msg, sizeof(this->lastMsg) - 1);
    this->lastMsg[sizeof(this->lastMsg) - 1] = '\0';
  }
}
