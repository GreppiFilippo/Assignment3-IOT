#ifndef __LOGGER__
#define __LOGGER__

#include "Arduino.h"

/**
 * @brief Service for logging messages.
 *
 */
class LoggerService
{
   public:
    /**
     * @brief Log a message.
     *
     * The message is prefixed with "lo:" to indicate it's a log entry.
     *
     * @param msg The message to log as a String.
     */
    void log(const String& msg);

    /**
     * @brief Log a message.
     *
     * The message is prefixed with "lo:" to indicate it's a log entry.
     *
     * @param msg The message to log as a Flash string.
     */
    void log(const __FlashStringHelper* msg);
};
extern LoggerService Logger;

#endif
