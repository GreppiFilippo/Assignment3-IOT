#ifndef __CONTEXT__
#define __CONTEXT__

#include <ArduinoJson.h>

#include "config.hpp"

/**
 * @brief Context class to hold system state
 */
class Context {
 private:
  unsigned int receivedValve;
  char lcdLines[LCD_ROWS][LCD_COLS + 1];
  unsigned long lastValidMsgTimestamp;
  unsigned long lastMsgSentTimestamp;
  bool buttonPressed;
  StaticJsonDocument<STORAGE_JSON_SIZE> jsonDoc;
  StaticJsonDocument<INPUT_JSON_SIZE> receivedJson;

 public:
  /**
   * @brief Construct a new Context object
   *
   */
  Context();

  // ========== Getters ==========
  /**
   * @brief Get the Received Valve Position
   *
   * This function returns the last received valve position from the CUS.
   * It must be set by calling setReceivedValvePosition() from a task.
   *
   * @return unsigned int Received valve position (0-100)
   */
  unsigned int getReceivedValvePosition() const;

  /**
   * @brief Get the LCD Line
   *
   * @param line Line number (0 to LCD_ROWS-1)
   * @return const char* Pointer to the string representing the LCD line
   */
  const char* getLCDLine(uint8_t line) const;

  /**
   * @brief Get the Last Valid Received Msg Timestamp object
   *
   * @return unsigned long Timestamp of the last valid message received from CUS
   */
  unsigned long getLastValidReceivedMsgTimestamp() const;

  /**
   * @brief Get the Last Msg Sent Timestamp object
   *
   * @return unsigned long Timestamp of the last message sent to CUS
   */
  unsigned long getLastMsgSentTimestamp() const;

  /**
   * @brief Set the Received Valve Position object
   *
   * This function sets the last received valve position from the CUS.
   * It is typically called by a task when a new command is received.
   *
   * @param valve Received valve position (0-100)
   */
  void setReceivedValvePosition(unsigned int valve);

  /**
   * @brief Set the LCD Line object
   *
   * @param line Line number (0 to LCD_ROWS-1)
   * @param msg Null-terminated string to set for the LCD line
   */
  void setLCDLine(uint8_t line, const char* msg);

  /**
   * @brief Set the Last Valid Received Msg Timestamp object
   *
   * @param timestamp Timestamp of the last valid message received from CUS
   */
  void setLastValidReceivedMsgTimestamp(unsigned long timestamp);

  /**
   * @brief Set the Last Msg Sent Timestamp object
   *
   * @param timestamp Timestamp of the last message sent to CUS
   */
  void setLastMsgSentTimestamp(unsigned long timestamp);

  /**
   * @brief Serialize the internal JSON data to a buffer
   *
   * @param commonBuf Pointer to the buffer where serialized data will be stored
   * @param bufSize Size of the buffer in bytes
   * @return size_t Number of bytes written to the buffer
   */
  size_t serializeData(void* commonBuf, size_t bufSize);

  /**
   * @brief Clear the internal JSON data
   *
   */
  void clearData();

  /**
   * @brief Set the Field object in the internal JSON data
   *
   * @param key  Key of the field to set
   * @param value Value to set for the field
   */
  void setField(const char* key, bool value);

  /**
   * @brief Set the Field object in the internal JSON data
   *
   * @param key  Key of the field to set
   * @param value Value to set for the field
   */
  void setField(const char* key, int value);

  /**
   * @brief Set the Field object in the internal JSON data
   *
   * @param key  Key of the field to set
   * @param value Value to set for the field
   */
  void setField(const char* key, unsigned int value);

  /**
   * @brief Set the Button Pressed object.
   *
   * @param pressed True if the button was pressed, false otherwise
   */
  void setButtonPressed(bool pressed);

  /**
   * @brief Consume the Button Pressed event.
   *
   * @return true if the button was pressed since the last call.
   * @return false otherwise.
   */
  bool consumeButtonPressed();

  /**
   * @brief Get the Received Json object
   *
   * @return StaticJsonDocument<INPUT_JSON_SIZE>&  Reference to the received
   * JSON document
   */
  StaticJsonDocument<INPUT_JSON_SIZE>& getReceivedJson();
};

#endif
