#ifndef __TASK__
#define __TASK__

/**
 * @brief Abstract class representing a generic task.
 *
 */
class Task
{
   public:
    /**
     * @brief Initialize the task.
     *
     */
    virtual void init() {};

    /**
     * @brief Perform a tick of the task.
     *
     */
    virtual void tick() = 0;
};

#endif  // __TASK__
