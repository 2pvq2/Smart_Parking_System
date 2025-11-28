#ifndef SENSOR_HANDLER_H
#define SENSOR_HANDLER_H

#include <Arduino.h>
#include "../include/pin_definitions.h"

// Khởi tạo các chân cảm biến (INPUT)
void setupSensors();

// Kiểm tra trạng thái cảm biến của từng làn
// laneNum: 1 (Làn vào) hoặc 2 (Làn ra)
// Trả về: true nếu có vật cản (xe đang chắn), false nếu không
bool isSensorActive(int laneNum);

#endif