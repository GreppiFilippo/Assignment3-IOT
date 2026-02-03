#ifndef __LCD__
#define __LCD__

#include <Arduino.h>
#include <LiquidCrystal_I2C.h>

/**
 * @brief LCD display handler
 *
 */
class LCD {
 private:
  LiquidCrystal_I2C* _lcd;
  uint8_t _cols;
  uint8_t _rows;
  uint8_t _addr;

 public:
  /**
   * @brief Construct a new LCD object
   *
   * @param addr The I2C address of the LCD
   * @param cols Number of columns
   * @param rows Number of rows
   */
  LCD(uint8_t addr, uint8_t cols, uint8_t rows);

  /**
   * @brief Print a message to the LCD on the second line, handling word
   * wrapping
   *
   * @param message The message to print
   */
  void print(const char* message, int line);

  /**
   * @brief Clear the LCD display
   *
   */
  void clear();
};

#endif /* __LCD__ */