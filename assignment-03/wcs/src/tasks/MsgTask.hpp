#ifndef __MSG_TASK__
#define __MSG_TASK__

#include <Arduino.h>
#include <ArduinoJson.h>

#include "kernel/MsgService.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

/**
 * @brief Task that continuously consumes messages from serial
 * and stores them in Context's message queue.
 * Also periodically sends JSON state updates to serial.
 */
class MsgTask : public Task {
 private:
  Context* pContext;
  MsgServiceClass* pMsgService;
  unsigned long lastJsonSent;

 public:
  /**
   * @brief Constructor for MsgTask.
   * @param pContext Pointer to the shared system context.
   * @param pMsgService Pointer to the messaging service.
   */
  MsgTask(Context* pContext, MsgServiceClass* pMsgService);

  /**
   * @brief Task execution method called by the scheduler when the task runs.
   *
   * Processes incoming messages and sends periodic JSON updates.
   *
   */

  void tick() override;
};

#endif