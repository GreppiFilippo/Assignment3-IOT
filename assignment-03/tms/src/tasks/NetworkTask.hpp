#ifndef __NETWORK_TASK__
#define __NETWORK_TASK__

#include <devices/Light.hpp>

#include "kernel/Task.hpp"
#include "kernel/services/ConnectionService.hpp"
#include "model/Context.hpp"

class NetworkTask : public Task
{
   private:
    ConnectionService* pConnectionService;
    Context* pContext;
    Light* pAliveLight;
    Light* pErrorLight;

    bool justEntered;
    unsigned long stateTimestamp;
    unsigned long lastSentTime;

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
    /**
     * @brief Construct a new Network Task object
     *
     * @param pConnectionService the connection service
     * @param pContext the context
     */
    NetworkTask(ConnectionService* pConnectionService, Light* pAliveLight, Light* pErrorLight,
                Context* pContext);
    void init() override;
    void tick() override;

   private:
    void setState(State newState);
    long elapsedTimeInState();
    bool checkAndSetJustEntered();
    void sendData();
};

#endif  // __NETWORK_TASK__