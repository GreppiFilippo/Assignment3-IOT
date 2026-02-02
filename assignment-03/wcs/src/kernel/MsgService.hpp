#ifndef __MSGSERVICE__
#define __MSGSERVICE__

#include <Arduino.h>

#define MSG_SERVICE_QUEUE_SIZE 4

class Msg
{
   private:
    String content;

   public:
    Msg() : content("") {}
    void setContent(const char* c) { content = c; }
    const String& getContent() const { return content; }
};

class MsgServiceClass
{
   private:
    Msg queue[MSG_SERVICE_QUEUE_SIZE];
    int8_t qHead, qTail, qCount;

   public:
    void init(unsigned long baudRate);
    bool isMsgAvailable();

    /**
     * @brief Receive a message from the queue.
     *
     * Don't delete or free the returned pointer, it's managed by the MsgService.
     * @return nullptr if no message is available.
     *
     * @return Msg* Pointer to the message.
     */
    Msg* receiveMsg();

    /**
     * @brief Send a message.
     *
     * @param msg Message to send.
     */
    void sendMsg(const String& msg);

    /**
     * @brief Send a message from flash memory.
     *
     * @param msg Message to send.
     */
    void sendMsg(const __FlashStringHelper* msg);

    /**
     * @brief Send a raw message.
     *
     * @param msg Message to send.
     * @param newline Whether to append a newline at the end.
     */
    void sendMsgRaw(const char* msg, bool newline);

    /**
     * @brief Send a raw message from flash memory.
     *
     * @param msg Message to send.
     * @param newline Whether to append a newline at the end.
     */
    void sendMsgRaw(const __FlashStringHelper* msg, bool newline);

    /**
     * @brief Enqueue a message.
     *
     * @param content Content of the message.
     * @return true if the message was successfully enqueued.
     * @return false if the queue is full.
     */
    bool enqueueMsg(const char* content);
};

extern MsgServiceClass MsgService;

#endif