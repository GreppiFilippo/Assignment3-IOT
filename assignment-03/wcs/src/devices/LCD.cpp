#include "LCD.hpp"

#include "config.hpp"
#include "kernel/Logger.hpp"

LCD::LCD(uint8_t addr, uint8_t cols, uint8_t rows) {
  _lcd = new LiquidCrystal_I2C(addr, cols, rows);
  _lcd->init();
  _lcd->backlight();
  _cols = cols;
  _rows = rows;
}

void LCD::print(const char* message, int line) {
  if (line < 0 || line >= _rows) {
    Logger.log(F("LCD_ERR"));
    return;
  }
  this->clear();
  _lcd->setCursor(0, line);
  _lcd->print(message);
}

void LCD::clear() { _lcd->clear(); }