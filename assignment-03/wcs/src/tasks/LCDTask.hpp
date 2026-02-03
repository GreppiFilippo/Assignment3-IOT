#ifndef __LCD_TASK__
#define __LCD_TASK__

#include "config.hpp"
#include "devices/LCD.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

#define LCD_BUFFER_SIZE (LCD_COLS * LCD_ROWS + 1)

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
  float lastValvePos;
  char lastMsg[LCD_BUFFER_SIZE];

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
