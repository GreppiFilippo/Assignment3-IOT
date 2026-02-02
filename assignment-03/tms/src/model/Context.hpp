#ifndef __CONTEXT__
#define __CONTEXT__

#include "kernel/Message.hpp"

#define MAX_PENDING_MESSAGES 10

class Context
{
   private:
    float waterLevel;
    
    Message pendingMessages[MAX_PENDING_MESSAGES];
    int messageCount;

   public:
    Context();
    void setWaterLevel(float level);
    float getWaterLevel() const;
    
    // Message queue management
    void addMessage(const char* topic, const char* payload);
    Message** getMessages();
    void clearMessages();
    int getMessageCount() const;
};

#endif  // __CONTEXT__
