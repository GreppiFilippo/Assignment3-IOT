#include "MsgService.hpp"

static char serialBuffer[128];
static size_t serialBufferIndex = 0;

MsgServiceClass MsgService;

void MsgServiceClass::init(unsigned long baudRate)
{
    Serial.begin(baudRate);
    qHead = 0;
    qTail = 0;
    qCount = 0;
    serialBufferIndex = 0;
}

bool MsgServiceClass::isMsgAvailable() { return qCount > 0; }

Msg* MsgServiceClass::receiveMsg()
{
    if (qCount == 0)
        return nullptr;
    Msg* msg = &queue[qHead];
    qHead = (qHead + 1) % MSG_SERVICE_QUEUE_SIZE;
    qCount--;
    return msg;
}

void MsgServiceClass::sendMsg(const String& msg) { Serial.println(msg); }

void MsgServiceClass::sendMsg(const __FlashStringHelper* msg) { Serial.println(msg); }

void MsgServiceClass::sendMsgRaw(const char* msg, bool newline)
{
    if (newline)
        Serial.println(msg);
    else
        Serial.print(msg);
}

void MsgServiceClass::sendMsgRaw(const __FlashStringHelper* msg, bool newline)
{
    if (newline)
        Serial.println(msg);
    else
        Serial.print(msg);
}

bool MsgServiceClass::enqueueMsg(const char* content)
{
    if (qCount >= MSG_SERVICE_QUEUE_SIZE)
        return false;

    queue[qTail].setContent(content);
    qTail = (qTail + 1) % MSG_SERVICE_QUEUE_SIZE;
    qCount++;
    return true;
}

void serialEvent()
{
    while (Serial.available())
    {
        char ch = (char)Serial.read();
        if (ch == '\n')
        {
            if (serialBufferIndex > 0)
            {
                serialBuffer[serialBufferIndex] = '\0';
                MsgService.enqueueMsg(serialBuffer);
            }
            serialBufferIndex = 0;
        }
        else if (ch != '\r' && serialBufferIndex < sizeof(serialBuffer) - 1)
        {
            serialBuffer[serialBufferIndex++] = ch;
        }
    }
}