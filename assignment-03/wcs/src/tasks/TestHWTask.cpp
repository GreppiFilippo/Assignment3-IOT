#include "tasks/TestHWTask.hpp"

TestHWTask::TestHWTask(HWPlatform* pHW) : pHW(pHW) {}

void TestHWTask::tick() { pHW->test(); }
