#ifndef __CONTEXT__
#define __CONTEXT__

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

 private:
  Mode mode;
  int valveOpening;
};
#endif