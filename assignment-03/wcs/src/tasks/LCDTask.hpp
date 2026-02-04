#ifndef __LCD_TASK__
#define __LCD_TASK__

#include "config.hpp"
#include "devices/LCD.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

/**
 * @brief Task to manage the LCD display.
 *
 * This task periodically updates the LCD with relevant information from the
 * system context.
 */
class LCDTask : public Task {
 private:
  Context* pContext;
  LCD* lcd;
  char lastLines[LCD_ROWS][LCD_COLS + 1];

 public:
  /**
   * @brief Construct a new LCDTask object
   *
   * @param lcd the LCD device to manage
   * @param pContext the system context to read messages from
   */
  LCDTask(LCD* lcd, Context* pContext);

  /**
   * @brief Task execution method called by the scheduler when the task runs.
   * Updates the LCD display if the message has changed.
   */
  void tick() override;
};

#endif  // __LCD_TASK__
