#ifndef __TASK__
#define __TASK__

/**
 * @brief Abstract base class representing a schedulable task.
 *
 */
class Task
{
   private:
    unsigned long myPeriod;
    unsigned long timeElapsed;
    bool active;
    bool periodic;
    bool completed;

   public:
    /**
     * Default constructor. Initializes the task as inactive.
     */
    Task() { this->active = false; }

    /**
     * Initialize the task as periodic with the given period.
     *
     * @param period period (milliseconds) at which the task should run
     */
    virtual void init(unsigned long period)
    {
        this->myPeriod = period;
        this->periodic = true;
        this->active = true;
        this->timeElapsed = 0;
    }

    /**
     * Initialize the task as aperiodic (one-shot).
     * Marks the task active and not completed.
     */
    virtual void init()
    {
        this->timeElapsed = 0;
        this->periodic = false;
        this->active = true;
        this->completed = false;
    }

    /**
     * Task execution method called by the scheduler when the task runs.
     * Concrete tasks must implement this method.
     */
    virtual void tick() = 0;

    /**
     * Update the internal elapsed time and check if the period has passed.
     * This is intended for periodic tasks: the scheduler should call it
     * with the scheduler base period.
     *
     * @param basePeriod elapsed time since last update (milliseconds)
     * @return true if the task period has elapsed and the task should run
     */
    bool updateAndCheckTime(unsigned long basePeriod)
    {
        this->timeElapsed += basePeriod;
        if (this->timeElapsed >= this->myPeriod)
        {
            this->timeElapsed = 0;
            return true;
        }
        else
        {
            return false;
        }
    }

    /**
     * Mark the task as completed and deactivate it (for one-shot tasks).
     */
    void setCompleted()
    {
        this->completed = true;
        this->active = false;
    }

    /**
     * Check whether the task has completed (for aperiodic tasks).
     * @return true if completed, false otherwise
     */
    bool isCompleted() { return this->completed; }

    /**
     * Check whether the task is periodic.
     * @return true if periodic, false if aperiodic
     */
    bool isPeriodic() { return this->periodic; }

    /**
     * Check whether the task is currently active.
     * @return true if active, false otherwise
     */
    bool isActive() { return this->active; }

    /**
     * Get the configured period for periodic tasks.
     * @return period in milliseconds
     */
    unsigned long getPeriod() { return this->myPeriod; }

    /**
     * Activate or deactivate the task. When activated, elapsed time is reset.
     * @param active true to activate the task, false to deactivate
     */
    virtual void setActive(bool active)
    {
        timeElapsed = 0;
        this->active = active;
    }
};

#endif /* _TASK_ */
