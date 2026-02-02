#ifndef __POT__
#define __POT__

class Potentiometer {
 public:
  /**
   * @brief Construct a new Potentiometer object
   *
   * @param pin Analog pin connected to the potentiometer
   */
  Potentiometer(int pin);

  float getValue();

  virtual void sync();
  long getLastSyncTime();

 protected:
  void updateSyncTime(long time);

 private:
  long lastTimeSync;
  int pin;
  float value;
};

#endif
