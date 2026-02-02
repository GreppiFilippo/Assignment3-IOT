#ifndef __WIFI_CONNECTION_SERVICE__
#define __WIFI_CONNECTION_SERVICE__

#include "kernel/services/NetworkConnectionService.hpp"

class WiFiConnectionService : public NetworkConnectionService
{
   private:
    const char* ssid;
    const char* password;

   public:
    WiFiConnectionService(const char* ssid, const char* password);

    void init() override;
    void connect() override;
};

#endif  // __WIFI_CONNECTION_SERVICE__
