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

    // 1. Se è già connesso, non fare nulla
    if (status == WL_CONNECTED)
    {
            Logger.log(F("[WiFi] Connected"));
            Logger.log(String("[WiFi] IP: ") + WiFi.localIP().toString());
        return;
    }

    // 2. Se arriviamo qui, non siamo connessi. Proviamo a connetterci.
    Logger.log(F("[WiFi] Connecting"));
    
    // Avviamo il tentativo
    WiFi.begin(ssid, password);

    // 3. ASPETTIAMO FINO A 5 SECONDI (5*1000ms) è il tempo perché l'esp si connetta
    int maxAttempts = 5; 
    for(int i = 0; i < maxAttempts; i++)
    {
        status = WiFi.status();
        if (status == WL_CONNECTED)
        {
            Logger.log(F("[WiFi] Connected"));
            Logger.log(String("[WiFi] IP: ") + WiFi.localIP().toString());
            return; 
        }
        delay(1000); 
        // Opzionale: stampa un puntino sulla seriale per vedere che non è bloccato
        Logger.log("[WiFi] Attempt " + String(i + 1) + "/" + String(maxAttempts)); 
    }

    // 4. Se dopo 5 secondi non è successo nulla
    Serial.println(""); 
    Logger.log(F("[WiFi] Connection timed out after 5s"));
}

bool WiFiConnectionService::isConnected()
{
    return WiFi.status() == WL_CONNECTED;
}

Client* WiFiConnectionService::getClient()
{
    return &wifiClient;
}