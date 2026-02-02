#ifndef __WIFI_CONNECTION_SERVICE__
#define __WIFI_CONNECTION_SERVICE__

#include <WiFi.h>

#include "kernel/services/NetworkConnectionService.hpp"

class WiFiConnectionService : public NetworkConnectionService
{
   private:
    const char* ssid;
    const char* password;
    WiFiClient wifiClient;

   public:
    WiFiConnectionService(const char* ssid, const char* password);

    void init() override;
    void connect() override;
    bool isConnected() override;
    Client* getClient() override;
};

#endif  // __WIFI_CONNECTION_SERVICE__
