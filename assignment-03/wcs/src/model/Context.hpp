#include "kernel/MsgService.hpp"

#ifndef __CONTEXT__
#define __CONTEXT__

#include <ArduinoJson.h>

/**
 * @brief Context class to hold system state and manage commands from CUS
 *
 */
class Context {
 public:
  enum Mode { UNCONNECTED, AUTOMATIC, MANUAL };

  Context();

  // Command handlers - called by MsgTask when CUS sends commands
  void cmdSetValve(JsonDocument& doc);
  void cmdSetMode(JsonDocument& doc);
  void cmdGetStatus(JsonDocument& doc);

  // Command consumption - used by tasks to execute commands
  bool hasValveCommand();
  unsigned int consumeValveCommand();
  bool hasModeCommand();
  Mode consumeModeCommand();

  // State getters for event serialization
  Mode getMode() const;
  unsigned int getValveOpening() const;
  bool wasButtonPressed();
  float getPotValue() const;
  const char* getLCDMessage() const;

  // State setters - used by tasks to update local state
  void setValveOpening(unsigned int opening);
  void setPotValue(float value);
  void setButtonPressed();
  void setLCDMessage(const char* msg);
  void setMode(Mode mode);

  // Command registry
  typedef void (Context::*CmdHandler)(JsonDocument&);
  struct CmdEntry {
    const char* name;
    CmdHandler handler;
  };
  static const CmdEntry* getCmdTable();
  static int getCmdTableSize();

 private:
  // Command buffers - set by MsgTask, consumed by tasks
  struct ValveCommand {
    bool pending;
    unsigned int position;
    unsigned long timestamp;
  } valveCmd;

  struct ModeCommand {
    bool pending;
    Mode mode;
    unsigned long timestamp;
  } modeCmd;

  // Current state
  Mode mode;
  unsigned int valveOpening;
  float potValue;
  bool buttonPressed;
  const char* lcdMessage;

  // Command table
  static const CmdEntry cmdTable[];
};

#endif