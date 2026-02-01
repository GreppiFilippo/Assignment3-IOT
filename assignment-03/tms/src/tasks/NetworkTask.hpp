#ifndef __NETWORK_TASK__
#define __NETWORK_TASK__

class NetworkTask
{
   private:
    /**
     * @brief Network Task State
     *
     */
    enum State
    {
        /// @brief Initial State
        CONNECTING,
        /// @brief Network is OK
        NETWORK_OK,
        /// @brief Network Error
        NETWORK_ERROR
    } state;

   public:
    NetworkTask(/* args */);
};

#endif  // __NETWORK_TASK__