#ifndef __LOGGER__
#define __LOGGER__

#include "Arduino.h"

/**
 * @brief Service for logging messages.
 */
class LoggerService {
 public:
  void log(const String& msg);
  void log(const __FlashStringHelper* msg);
};
extern LoggerService Logger;

#endif  // __LOGGER__
