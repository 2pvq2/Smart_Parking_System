#include "sensor_handler.h"

void setupSensors() {
    pinMode(IR_1_PIN, INPUT);
    pinMode(IR_2_PIN, INPUT);
}

bool isSensorActive(int laneNum) {
    int pin = (laneNum == 1) ? IR_1_PIN : IR_2_PIN;
    // Giả sử IR: LOW = Có vật cản
    return digitalRead(pin) == LOW;
}