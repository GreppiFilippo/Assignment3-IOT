#ifndef __PROTOCOL_SERVICE__
#define __PROTOCOL_SERVICE__

#include "kernel/Message.hpp"
#include "kernel/services/NetworkConnectionService.hpp"

/**
 * @brief Service for managing application protocol connections (MQTT, HTTP, CoAP, etc.).
 *
 * @note This is an abstract class and should be inherited by specific protocol implementations.
 */
class ProtocolService
{
   protected:
    bool connected = false;
    NetworkConnectionService* networkService;

   public:
    /**
     * @brief Initialize the protocol service.
     */
    virtual void init() {};

    /**
     * @brief Establish the protocol connection.
     */
    virtual void connect() = 0;

    /**
     * @brief Send a message through the connection.
     *
     * @param msg The message to send
     * @return true if the message was sent successfully
     * @return false if the message failed to send
     */
    virtual bool send(Message* msg) = 0;

    /**
     * @brief Check if the service is connected.
     *
     * @return true if connected
     * @return false if not connected
     */
    bool isConnected() { return connected; }

    /**
     * @brief Process protocol service loop (e.g., keep-alive, message processing).
     */
    virtual void loop() {};
};

#endif  // __PROTOCOL_SERVICE__
