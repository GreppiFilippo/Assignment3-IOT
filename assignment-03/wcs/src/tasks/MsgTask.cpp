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
}

void MsgTask::tick() {
  static char commonBuf[128];
  static StaticJsonDocument<128> jsonDoc;

  this->pContext->cleanupExpired(millis());

  if (this->pMsgService->isMsgAvailable()) {
    Msg* msg = this->pMsgService->receiveMsg();
    if (msg) {
      const String& content = msg->getContent();
      if (content.length() > 0) {
        if (content.length() < sizeof(commonBuf)) {
          strcpy(commonBuf, content.c_str());
          char* jsonStart = strchr(commonBuf, '{');
          if (jsonStart) {
            jsonDoc.clear();
            DeserializationError err = deserializeJson(jsonDoc, jsonStart);
            if (err == DeserializationError::Ok) {
              if (jsonDoc.overflowed()) {
                Logger.log(F("JSON_OVR"));
              }
              const char* cmd = jsonDoc[COMMAND];

              if (!cmd) {
                for (JsonPair kv : jsonDoc.as<JsonObject>()) {
                  if (strcmp(kv.key().c_str(), COMMAND) == 0) {
                    if (kv.value().is<const char*>())
                      cmd = kv.value().as<const char*>();
                    break;
                  }
                }
              }

              if (cmd) {
                bool result = this->pContext->tryEnqueueMsg(cmd);
                Logger.log(result ? F("CMD_OK") : F("CMD_ERR"));
              } else {
                Logger.log(F("CMD_NULL"));
              }
            } else {
              Logger.log(F("JSON_ERR"));
            }
          }
        } else {
          Logger.log(F("MSG_OVR"));
        }
      }
    }
  }

  if (millis() - lastJsonSent >= JSON_UPDATE_PERIOD_MS) {
    jsonDoc.clear();
    this->pContext->serializeData(jsonDoc);
    jsonDoc[ALIVE] = true;
    serializeJson(jsonDoc, commonBuf, sizeof(commonBuf));

    this->pMsgService->sendMsgRaw(commonBuf, true);
    lastJsonSent = millis();
  }
}