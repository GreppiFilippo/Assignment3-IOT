#include "Logger.hpp"

void LoggerService::log(const String& msg)
{
    Serial.print("lo:");
    Serial.println(msg);
}

void LoggerService::log(const __FlashStringHelper* msg)
{
    Serial.print(F("lo:"));
    Serial.println(msg);
}
