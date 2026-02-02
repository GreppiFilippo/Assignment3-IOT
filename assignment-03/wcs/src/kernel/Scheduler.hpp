#ifndef __SCHEDULER__
#define __SCHEDULER__

#include "Task.hpp"

#define MAX_TASKS 50

/**
 * @brief Scheduler class for managing and executing tasks.
 *
 */
class Scheduler
{
   private:
    int basePeriod;
    int nTasks;
    Task* taskList[MAX_TASKS];

   public:
    /**
     * @brief Initialize the scheduler with a base period.
     *
     * @param basePeriod the base period
     */
    void init(int basePeriod);

    /**
     * @brief Add a task to the scheduler.
     *
     * @param task pointer to the task to add
     * @return true if the task was added successfully
     * @return false if the task could not be added
     */
    virtual bool addTask(Task* task);

    /**
     * @brief Schedule tasks according to their periods.
     *
     */
    virtual void schedule();
};

#endif
