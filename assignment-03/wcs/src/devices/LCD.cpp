#include "LCD.hpp"

#include "config.hpp"
#include "kernel/Logger.hpp"

LCD::LCD(uint8_t addr, uint8_t cols, uint8_t rows) {
  _lcd = new LiquidCrystal_I2C(addr, cols, rows);
  _lcd->init();
  _lcd->backlight();
  _cols = cols;
  _rows = rows;
  _lineWritten = new bool[rows];
  for (uint8_t i = 0; i < rows; i++) {
    _lineWritten[i] = false;
  }
}

void LCD::print(const char* message, int line) {
  if (line < 0 || line >= _rows) {
    Logger.log(F("LCD_ERR"));
    return;
  }
  
  // Check if any line needs clearing (first write to any line)
  bool needsClear = true;
  for (uint8_t i = 0; i < _rows; i++) {
    if (_lineWritten[i]) {
      needsClear = false;
      break;
    }
  }
  
  // Clear entire LCD only on first write
  if (needsClear) {
    _lcd->clear();
  } else {
    // Clear only the specific line by overwriting with spaces
    _lcd->setCursor(0, line);
    for (uint8_t i = 0; i < _cols; i++) {
      _lcd->print(' ');
    }
  }
  
  // Print the message
  _lcd->setCursor(0, line);
  _lcd->print(message);
  _lineWritten[line] = true;
}

void LCD::clear() { 
  _lcd->clear();
  // Reset tracking when manually cleared
  for (uint8_t i = 0; i < _rows; i++) {
    _lineWritten[i] = false;
  }
}