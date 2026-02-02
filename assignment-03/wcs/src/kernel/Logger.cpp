#include "Logger.hpp"

#include "MsgService.hpp"

void LoggerService::log(const String& msg)
{
    MsgService.sendMsgRaw("lo:", false);
    MsgService.sendMsgRaw(msg.c_str(), true);
}

void LoggerService::log(const __FlashStringHelper* msg)
{
    MsgService.sendMsgRaw("lo:", false);
    MsgService.sendMsgRaw(msg, true);
}
