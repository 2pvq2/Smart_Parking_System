#ifndef RFID_HANDLER_H
#define RFID_HANDLER_H

#include <Arduino.h>
#include <MFRC522.h>
#include <SPI.h>
#include "../include/pin_definitions.h"

// Khởi tạo 2 đầu đọc RFID
void setupRFID();

// Đọc UID từ đầu đọc chỉ định (1 hoặc 2)
String getCardUID(int readerNum);

#endif