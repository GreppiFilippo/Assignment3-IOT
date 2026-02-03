#include "kernel/MsgService.hpp"

#ifndef __CONTEXT__
#define __CONTEXT__

#include <ArduinoJson.h>

/**
 * @brief Context class to hold system state
 *
 */
class Context {
 private:
  float potValue;
  float valveOpening;
  const char* lcdMessage;
  bool isModeChangeRequested;
  unsigned int valvePosition;

 public:
  /**
   * @brief System modes
   *
   */
  enum Mode { UNCONNECTED, AUTOMATIC, MANUAL } mode;

  Context();

  /**
   * @brief Set requested valve opening
   *
   * @param opening
   */
  void setRequestedValveOpening(int opening);

  /**
   * @brief Change system mode
   *
   * @param mode New mode
   */
  void setMode(Mode mode);

  /**
   * @brief Get LCD message
   *
   * @return const char* LCD message
   */
  const char* getLCDMessage() const;

  /**
   * @brief Set LCD message
   *
   * @param msg New LCD message
   */
  void setLCDMessage(const char* msg);

  /**
   * @brief Get requested valve opening
   *
   * @return int Requested valve opening
   */
  int getRequestedValveOpening();

  /**
   * @brief Request mode change
   *
   */
  void requestModeChange();

  /**
   * @brief Serialize context data to JSON
   *
   * @param doc JSON document to serialize data into
   */
  void serializeData(JsonDocument& doc);

  /**
   * @brief Set the potentiometer Value
   *
   * @param value New potentiometer value
   */
  void setPotValue(float value);

  // TODO: to be changed
  Mode getMsgMode();
  unsigned int getMsgOpening();
};

#endif