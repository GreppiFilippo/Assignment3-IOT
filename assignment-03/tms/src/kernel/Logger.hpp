#ifndef __LOGGER_HPP__
#define __LOGGER_HPP__

/**
 * @brief A simple logger that outputs messages to the serial console
 *
 */
class Logger {
 public:
  /**
   * @brief Get the singleton instance of Logger
   *
   * @return Logger& The Logger instance
   */
  static Logger& instance();

  /**
   * @brief Log a message to the serial output
   *
   * @param message The message to log
   */
  void log(const char* message);

 private:
  Logger();
  Logger(const Logger&) = delete;
  Logger& operator=(const Logger&) = delete;
};

#endif  // __LOGGER_HPP__