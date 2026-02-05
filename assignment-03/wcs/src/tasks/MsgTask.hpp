#ifndef __MSG_TASK__
#define __MSG_TASK__

#include <Arduino.h>

#include "kernel/MsgService.hpp"
#include "kernel/Task.hpp"
#include "model/Context.hpp"

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
   * Processes incoming commands and sends events to CUS.
   *
   */
  void tick() override;
};

#endif