#ifndef __NETWORK_CONNECTION_SERVICE__
#define __NETWORK_CONNECTION_SERVICE__

#include <Client.h>

/**
 * @brief Service for managing physical network connections (WiFi, Ethernet, LoRa, etc.).
 *
 * @note This is an abstract class and should be inherited by specific network implementations.
 */
class NetworkConnectionService
{
    
   public:
    /**
     * @brief Initialize the network connection.
     */
    virtual void init() = 0;

    /**
     * @brief Establish the network connection.
     */
    virtual void connect() = 0;

    /**
     * @brief Check if the network is connected.
     *
     * @return true if connected
     * @return false if not connected
     */
    virtual bool isConnected() = 0;

    /**
     * @brief Get the Client instance for this network connection.
     *
     * @return Client* pointer to the client instance
     */
    virtual Client* getClient() = 0;
};

#endif  // __NETWORK_CONNECTION_SERVICE__
