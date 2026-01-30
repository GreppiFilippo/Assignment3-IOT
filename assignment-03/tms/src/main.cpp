// How to user FreeRTOS to run a task on a specific core of ESP32
/* void setup() {
  xTaskCreatePinnedToCore(Task1code, "Task1", 10000, NULL, 1, &Task1,
                          0);  // run new task in core one
  delay(500);
}

void loop() {}

void Task1code(void* pvParameters) {
  for (;;) {
    Serial.println("Task1 is running on core " + String(xPortGetCoreID()));
    delay(1000);
  }
} */

TaskHandle_t Task1;

void setup()
{
#ifdef HW_TEST
// Test code here
#else

#endif
}

void loop() {}