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
  static char commonBuf[max(OUTPUT_JSON_SIZE, INPUT_JSON_SIZE)];

  // ======== INCOMING COMMANDS FROM CUS ========
  if (this->pMsgService->isMsgAvailable()) {
    Msg* msg = this->pMsgService->receiveMsg();
    if (msg) {
      const String& content = msg->getContent();
      if (content.length() > 0 && content.length() < sizeof(commonBuf)) {
        strcpy(commonBuf, content.c_str());
        char* jsonStart = strchr(commonBuf, '{');

        if (jsonStart) {
          StaticJsonDocument<INPUT_JSON_SIZE>& jsonDoc =
              this->pContext->getReceivedJson();
          jsonDoc.clear();
          DeserializationError err = deserializeJson(jsonDoc, jsonStart);

          if (err == DeserializationError::Ok) {
            // Update timestamp for timeout detection
            this->pContext->setLastValidReceivedMsgTimestamp(millis());
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
  // Periodic heartbeat with system status
  if (millis() - lastJsonSent >= JSON_UPDATE_PERIOD_MS) {
    this->pContext->serializeData(commonBuf, sizeof(commonBuf));
    this->pMsgService->sendMsgRaw(commonBuf, true);
    lastJsonSent = millis();
    this->pContext->setLastMsgSentTimestamp(lastJsonSent);
  }
}
