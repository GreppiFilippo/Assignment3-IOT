#ifndef __CONFIG__
#define __CONFIG__

#define SERVO_PIN 9
#define POT_PIN A0
#define LCD_ADDR 0x27
#define LCD_COLS 20
#define LCD_ROWS 4
#define BUTTON_PIN 7

#define LCD_AUTOMATIC_MODE "Automatic Mode"
#define LCD_MANUAL_MODE "Manual Mode"
#define LCD_UNCONNECTED "Unconnected"
#define BAUD_RATE 115200

#define SCHED_BASE_PERIOD 50
#define CONNECTION_TASK_PERIOD 500
#define SYSTEM_TASK_PERIOD 200
#define VALVE_TASK_PERIOD 100
#define VALVE_MAX_ANGLE 90
#define VALVE_MIN_ANGLE 0

#define MSEC_PER_PERCENT 6

#endif  // __CONFIG__