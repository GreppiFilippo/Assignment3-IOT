#include "tasks/LCDTask.hpp"

#include "config.hpp"

LCDTask::LCDTask(LCD* lcd, Context* pContext) {
  this->lcd = lcd;
  this->pContext = pContext;
  for (uint8_t i = 0; i < LCD_ROWS; i++) {
    this->lastLines[i][0] = '\0';
  }
}

void LCDTask::tick() {
  for (uint8_t line = 0; line < LCD_ROWS; line++) {
    const char* currentMsg = pContext->getLCDLine(line);
    
    if (currentMsg == nullptr) {
      continue;
    }
    
    if (strcmp(currentMsg, lastLines[line]) != 0) {
      lcd->print(currentMsg, line);
      strncpy(lastLines[line], currentMsg, LCD_COLS);
      lastLines[line][LCD_COLS] = '\0';
    }
  }
}
