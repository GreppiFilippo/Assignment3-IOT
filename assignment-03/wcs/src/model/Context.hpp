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

  typedef void (Context::*CmdHandler)(JsonDocument&);

  struct CmdEntry {
    const char* name;
    CmdHandler handler;
  };

 public:
  /**
   * @brief Construct a new Context object.
   *
   */
  Context();

  /**
   * @brief Get the system Mode.
   *
   * @return Mode Current system mode
   */
  Mode getMode() const;

  /**
   * @brief Get the Valve Target Position requested.
   *
   * @return unsigned int
   */
  unsigned int getValveTargetPosition() const;

  /**
   * @brief Check if the button was pressed since last check.
   *
   * @return true if pressed
   * @return false if not pressed
   */
  bool wasButtonPressed();

  /**
   * @brief Get the value of the potentiometer.
   *
   * @return float Potentiometer value
   */
  float getPotValue() const;

  // TODO: check to write into multiple lines
  /**
   * @brief Get the LCD Message
   *
   * @return const char*
   */
  const char* getLCDMessage() const;
  // END TODO

  // State setters - used by tasks to update local state
  /**
   * @brief Set the Valve Opening
   *
   * Thi
   *
   * @param opening
   */
  void setRequestedValveOpening(unsigned int opening);

  /**
   * @brief Set the Pot Value to validate
   *
   * @param value the new potentiometer value
   */
  void setPotValueToValidate(float value);

  /**
   * @brief Set the Button Pressed flag
   *
   */
  void setButtonPressed();

  /**
   * @brief Set the LCD Message
   *
   * @param msg New message to display
   */
  void setLCDMessage(const char* msg);

  /**
   * @brief Set the system Mode.
   *
   * @param mode New system mode
   */
  void setMode(Mode mode);

  /**
   * @brief Get the Last Valid Msg Timestamp
   *
   * @return Timestamp of the last valid message received from CUS
   */
  unsigned long getLastValidMsgTimestamp();

  // ============================
  // ===== Command registry =====
  // ============================
  // Command handlers - called by MsgTask when CUS sends commands
  void cmdSetValve(JsonDocument& doc);
  void cmdSetMode(JsonDocument& doc);

  // Command consumption - used by tasks to execute commands
  bool hasValveCommand();
  unsigned int consumeValveCommand();
  bool hasModeCommand();
  Mode consumeModeCommand();

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
  unsigned long lastValidMsgTimestamp;

  // Command table
  static const CmdEntry cmdTable[];
};

#endif
