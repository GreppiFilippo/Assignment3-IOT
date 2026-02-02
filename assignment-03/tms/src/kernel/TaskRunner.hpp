#ifndef __TASK_RUNNER__
#define __TASK_RUNNER__

#include "Task.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/**
 * @brief TaskRunner schedules and executes a logical Task using FreeRTOS.
 *
 * Keeps the task logic independent from FreeRTOS.
 */
class TaskRunner
{
   public:
    /**
     * @brief Construct a new TaskRunner and start the FreeRTOS task
     *
     * @param task      Pointer to the logical Task
     * @param name      Task name
     * @param stack     Stack size in words
     * @param priority  FreeRTOS priority
     * @param period    Task period in ticks
     * @param core      ESP32 core (0 or 1, default tskNO_AFFINITY)
     */
    TaskRunner(Task* task, const char* name, uint32_t stack, UBaseType_t priority,
               TickType_t period, BaseType_t core = tskNO_AFFINITY)
        : task(task), period(period)
    {
        xTaskCreatePinnedToCore(taskEntryPoint, name, stack, this, priority, &handle, core);
    }

   private:
    static void taskEntryPoint(void* arg)
    {
        auto self = static_cast<TaskRunner*>(arg);

        // Call task initialization once
        self->task->init();

        // Run the task periodically
        for (;;)
        {
            self->task->tick();
            vTaskDelay(self->period);
        }
    }

    Task* task;           // Pointer to logical task (FSM/logic)
    TickType_t period;    // Period in ticks
    TaskHandle_t handle;  // Optional handle to interact with the task
};

#endif  // __TASK_RUNNER__
