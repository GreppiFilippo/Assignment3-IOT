#ifndef __TEST_HW_TASK__
#define __TEST_HW_TASK__

#include "kernel/Task.hpp"
#include "model/HWPlatform.hpp"

class TestHWTask : public Task {
 public:
  TestHWTask(HWPlatform* pHW);
  void tick();

 private:
  HWPlatform* pHW;
};

#endif