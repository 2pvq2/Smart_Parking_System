#ifndef DEVICE_CONTROL_H
#define DEVICE_CONTROL_H

#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>
#include "../include/pin_definitions.h"

void setupDevices();
void showLCD(String line1, String line2);

// Điều khiển Barrier (1 hoặc 2)
void openBarrier(int laneNum);
void closeBarrier(int laneNum);

// Điều khiển Còi (1 hoặc 2)
void beep(int laneNum, int duration = 200);

#endif