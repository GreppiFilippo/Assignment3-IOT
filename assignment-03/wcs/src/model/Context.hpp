#include "kernel/MsgService.hpp"

#ifndef __CONTEXT__
#define __CONTEXT__

/**
 * @brief Context class to hold system state
 *
 */
class Context {
 public:
  enum Mode { UNCONNECTED, AUTOMATIC, MANUAL };

  Msg lastMsg;
  unsigned int valvePosition;

  Context();

  void setButtonPressed();

  /**
   * @brief Check if system is connected
   *
   * @return true if connected
   * @return false if not connected
   */
  bool isConnected();

  void setValveOpening(unsigned int opening);
  void setMode(Mode mode);
  const char* getLCDMessage() const;
  void setLCDMessage(const char* msg);
  unsigned int getValveOpening();
  unsigned int getMsgOpening();
  Mode getMsgMode();
  void onBtnPressed();

 private:
  float potValue;
  Mode mode;
  float valveOpening;
  const char* lcdMessage;
  bool buttonPressed;
};

#endif