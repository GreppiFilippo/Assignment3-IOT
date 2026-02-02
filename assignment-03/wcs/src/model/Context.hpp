#ifndef __CONTEXT__
#define __CONTEXT__

/**
 * @brief Context class to hold system state
 *
 */
class Context {
 public:
  enum Mode { UNCONNECTED, AUTOMATIC, MANUAL };
  Context();
  int getValveOpening();
  Mode getMode();

  /**
   * @brief Register button input
   *
   */
  void setButtonPressed();

  /**
   * @brief Check if system is connected
   *
   * @return true if connected
   * @return false if not connected
   */
  bool isConnected();

  void setValveOpening(float opening);
  void setMode(Mode mode);

  const char* getLCDMessage() const;
  void setLCDMessage(const char* msg);

 private:
  Mode mode;
  float valveOpening;
};

#endif