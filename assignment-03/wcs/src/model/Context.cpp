#include "Context.hpp"

#include <ArduinoJson.h>

#include "config.hpp"

Context::Context() {
  this->receivedValve = 0;
  this->lastValidMsgTimestamp = 0;
  this->lastMsgSentTimestamp = 0;
  this->buttonPressed = false;

  for (uint8_t i = 0; i < LCD_ROWS; i++) {
    this->lcdLines[i][0] = '\0';
  }
}

unsigned int Context::getReceivedValvePosition() const { return receivedValve; }

const char* Context::getLCDLine(uint8_t line) const {
  if (line >= LCD_ROWS) {
    return nullptr;
  }
  return lcdLines[line];
}

unsigned long Context::getLastValidReceivedMsgTimestamp() const {
  return lastValidMsgTimestamp;
}

unsigned long Context::getLastMsgSentTimestamp() const {
  return lastMsgSentTimestamp;
}

void Context::setReceivedValvePosition(unsigned int valve) {
  receivedValve = valve;
}

void Context::setLCDLine(uint8_t line, const char* msg) {
  if (line >= LCD_ROWS) {
    return;
  }
  strncpy(lcdLines[line], msg, LCD_COLS);
  lcdLines[line][LCD_COLS] = '\0';
}

void Context::setLastValidReceivedMsgTimestamp(unsigned long timestamp) {
  lastValidMsgTimestamp = timestamp;
}

void Context::setLastMsgSentTimestamp(unsigned long timestamp) {
  lastMsgSentTimestamp = timestamp;
}

size_t Context::serializeData(void* commonBuf, size_t bufSize) {
  return serializeJson(jsonDoc, commonBuf, bufSize);
}

void Context::clearData() { jsonDoc.clear(); }

void Context::setField(const char* key, bool value) { jsonDoc[key] = value; }

void Context::setField(const char* key, int value) { jsonDoc[key] = value; }

void Context::setField(const char* key, unsigned int value) {
  jsonDoc[key] = value;
}

void Context::setButtonPressed(bool pressed) {
  if (pressed) {
    buttonPressed = true;
  }
}

bool Context::consumeButtonPressed() {
  bool result = buttonPressed;
  buttonPressed = false;
  return result;
}

StaticJsonDocument<INPUT_JSON_SIZE>& Context::getReceivedJson() {
  return receivedJson;
}

JsonObject Context::getOrCreateNestedObject(const char* key) {
  if (!jsonDoc.containsKey(key)) {
    return jsonDoc.createNestedObject(key);
  }
  return jsonDoc[key].as<JsonObject>();
}
