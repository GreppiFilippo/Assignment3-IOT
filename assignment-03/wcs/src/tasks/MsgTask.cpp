#include "MsgTask.hpp"

#include <Arduino.h>

#include "config.hpp"
#include "kernel/Logger.hpp"
#include "kernel/MsgService.hpp"
#include "model/Context.hpp"

MsgTask::MsgTask(Context* pContext, MsgServiceClass* pMsgService) {
  this->pContext = pContext;
  this->pMsgService = pMsgService;
  this->lastJsonSent = millis();
  this->lastPotValue = -1.0;
}

void MsgTask::tick() {
  static char commonBuf[128];
  static StaticJsonDocument<128> jsonDoc;

  // ======== INCOMING COMMANDS FROM CUS ========
  if (this->pMsgService->isMsgAvailable()) {
    Msg* msg = this->pMsgService->receiveMsg();
    if (msg) {
      const String& content = msg->getContent();
      if (content.length() > 0 && content.length() < sizeof(commonBuf)) {
        strcpy(commonBuf, content.c_str());
        char* jsonStart = strchr(commonBuf, '{');
        
        if (jsonStart) {
          jsonDoc.clear();
          DeserializationError err = deserializeJson(jsonDoc, jsonStart);
          
          if (err == DeserializationError::Ok) {
            // Command dispatch using lookup table
            const char* cmd = jsonDoc["cmd"];
            
            if (cmd) {
              bool handled = false;
              const Context::CmdEntry* cmdTable = Context::getCmdTable();
              int tableSize = Context::getCmdTableSize();
              
              for (int i = 0; i < tableSize; i++) {
                if (strcmp(cmd, cmdTable[i].name) == 0) {
                  // Execute command handler
                  (pContext->*(cmdTable[i].handler))(jsonDoc);
                  handled = true;
                  break;
                }
              }
              
              if (!handled) {
                Logger.log(F("CMD_UNKNOWN"));
              }
            } else {
              Logger.log(F("CMD_NULL"));
            }
          } else {
            Logger.log(F("JSON_ERR"));
          }
        }
      } else if (content.length() >= sizeof(commonBuf)) {
        Logger.log(F("MSG_OVR"));
      }
    }
  }

  // ======== OUTGOING EVENTS TO CUS ========
  
  // Send button events immediately
  if (pContext->wasButtonPressed()) {
    jsonDoc.clear();
    jsonDoc["event"] = "button_pressed";
    jsonDoc["timestamp"] = millis();
    serializeJson(jsonDoc, commonBuf, sizeof(commonBuf));
    this->pMsgService->sendMsgRaw(commonBuf, true);
  }

  // Send potentiometer changes with throttling (> 5% change)
  float currentPot = pContext->getPotValue();
  if (lastPotValue < 0 || abs(currentPot - lastPotValue) >= 5.0) {
    jsonDoc.clear();
    jsonDoc["event"] = "pot_changed";
    jsonDoc["value"] = currentPot;
    jsonDoc["timestamp"] = millis();
    serializeJson(jsonDoc, commonBuf, sizeof(commonBuf));
    this->pMsgService->sendMsgRaw(commonBuf, true);
    lastPotValue = currentPot;
  }

  // Periodic heartbeat with system status
  if (millis() - lastJsonSent >= JSON_UPDATE_PERIOD_MS) {
    jsonDoc.clear();
    jsonDoc["event"] = "heartbeat";
    jsonDoc["mode"] = getModeString(pContext->getMode());
    jsonDoc["valve_pos"] = pContext->getValveOpening();
    jsonDoc["uptime"] = millis();
    
    serializeJson(jsonDoc, commonBuf, sizeof(commonBuf));
    this->pMsgService->sendMsgRaw(commonBuf, true);
    lastJsonSent = millis();
  }
}

const char* MsgTask::getModeString(Context::Mode mode) {
  switch (mode) {
    case Context::AUTOMATIC:
      return "AUTOMATIC";
    case Context::MANUAL:
      return "MANUAL";
    case Context::UNCONNECTED:
    default:
      return "UNCONNECTED";
  }
}