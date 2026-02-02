#ifndef __MESSAGE__
#define __MESSAGE__

#define PAYLOAD_SIZE 64

typedef struct Message
{
    const char* topic;
    char payload[PAYLOAD_SIZE];
} Message;

#endif  // __MESSAGE__
