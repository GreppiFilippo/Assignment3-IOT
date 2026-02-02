
#include "config.hpp"
#include "kernel/Logger.hpp"
#include "kernel/MsgService.hpp"
#include "kernel/Scheduler.hpp"
#include "model/Context.hpp"
#include "model/HWPlatform.hpp"
#include "tasks/ConnectionTask.hpp"
#include "tasks/LCDTask.hpp"
#include "tasks/SystemTask.hpp"
#include "tasks/TestHWTask.hpp"
#include "tasks/ValveTask.hpp"

#define __TESTING_HW__

// Comment out to run hardware testing task
// #define __TESTING_HW__

Scheduler sched;
HWPlatform* pHWPlatform;
Context* pContext;

void setup() {
  MsgService.init(BAUD_RATE);
  sched.init(SCHED_BASE_PERIOD);
  Logger.log(F(":::::: Water Channel Subsystem ::::::"));

  pHWPlatform = new HWPlatform();
  pHWPlatform->init();

#ifndef __TESTING_HW__
  pContext = new Context();

  Task* pConnectionTask = new ConnectionTask(pContext, &MsgService);
  pConnectionTask->init(CONNECTION_TASK_PERIOD);

  Task* pSystemTask = new SystemTask(pContext, pHWPlatform->getButton(),
                                     pHWPlatform->getPotentiometer());
  pSystemTask->init(SYSTEM_TASK_PERIOD);

  Task* pValveTask = new ValveTask(pContext, pHWPlatform->getServoMotor());
  pValveTask->init(VALVE_TASK_PERIOD);

  Task* pLcdTask = new LCDTask(pHWPlatform->getLCD(), pContext);
  pLcdTask->init(LCD_TASK_PERIOD);

  sched.addTask(pConnectionTask);
  sched.addTask(pSystemTask);
  sched.addTask(pValveTask);
  sched.addTask(pLcdTask);
#else
  /* Testing */
  Task* pTestHWTask = new TestHWTask(pHWPlatform);
  pTestHWTask->init(2000);
  sched.addTask(pTestHWTask);
#endif
}

void loop() { sched.schedule(); }
