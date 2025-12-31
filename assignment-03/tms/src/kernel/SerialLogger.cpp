#include <Arduino.h>
#include <esp32-hal.h>

#include "Logger.hpp"
#include "config.hpp"

Logger& Logger::instance() {
  static Logger inst;
  return inst;
}

Logger::Logger() {
  Serial.begin(BAUD);
  while (!Serial) {
  }
}

void Logger::log(const char* message) { Serial.println(message); }