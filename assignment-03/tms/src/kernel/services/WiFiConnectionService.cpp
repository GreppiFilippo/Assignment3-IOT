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
    wl_status_t status = WiFi.status();

    // 1. If already connected, do nothing
    if (status == WL_CONNECTED)
    {
        Logger.log(F("[WiFi] Connected"));
        char buffer[64];
        snprintf(buffer, sizeof(buffer), "[WiFi] IP: %s", WiFi.localIP().toString().c_str());
        Logger.log(buffer);
        return;
    }

    // 2. If we arrive here, not connected. Try to connect.
    Logger.log(F("[WiFi] Connecting"));

    // Start connection attempt
    WiFi.begin(ssid, password);

    // 3. WAIT UP TO 5 SECONDS for ESP to connect
    int maxAttempts = 5;
    char buffer[64];
    for (int i = 0; i < maxAttempts; i++)
    {
        status = WiFi.status();
        if (status == WL_CONNECTED)
        {
            Logger.log(F("[WiFi] Connected"));
            snprintf(buffer, sizeof(buffer), "[WiFi] IP: %s", WiFi.localIP().toString().c_str());
            Logger.log(buffer);
            return;
        }
        delay(1000);
        // Optional: print status to see it's not blocked
        snprintf(buffer, sizeof(buffer), "[WiFi] Attempt %d/%d", i + 1, maxAttempts);
        Logger.log(buffer);
    }

    // 4. If nothing happened after 5 seconds
    Serial.println("");
    Logger.log(F("[WiFi] Connection timed out after 5s"));
}

bool WiFiConnectionService::isConnected() { return WiFi.status() == WL_CONNECTED; }

Client* WiFiConnectionService::getClient() { return &wifiClient; }