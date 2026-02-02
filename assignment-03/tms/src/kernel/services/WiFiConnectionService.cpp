#include "kernel/services/WiFiConnectionService.hpp"

#include <WiFi.h>

#include "kernel/Logger.hpp"

WiFiConnectionService::WiFiConnectionService(const char* ssid, const char* password)
    : ssid(ssid), password(password)
{
}

void WiFiConnectionService::init()
{
    WiFi.mode(WIFI_STA);
    Logger.log(F("[WiFi] Initialized"));
}

void WiFiConnectionService::connect()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        connected = true;
        return;
    }

    if (WiFi.status() == WL_IDLE_STATUS)
    {
        Logger.log(F("[WiFi] Connecting..."));
        WiFi.begin(ssid, password);
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Logger.log(F("[WiFi] Connected"));
        Logger.log(String("[WiFi] IP: ") + WiFi.localIP().toString());
        connected = true;
    }
    else
    {
        connected = false;
    }
}
