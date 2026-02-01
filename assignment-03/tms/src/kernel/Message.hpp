#ifndef __MESSAGE__
#define __MESSAGE__

#include <Arduino.h>

#define OP_LEVEL_UPDATE 0x01
#define OP_SET_VALVE 0x02
#define OP_SET_MODE 0x03

struct Message
{
    uint8_t opcode;
    char payload[32];
};

#endif  // __MESSAGE__