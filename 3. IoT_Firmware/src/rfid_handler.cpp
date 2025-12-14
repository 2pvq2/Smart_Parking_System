#include "rfid_handler.h"

// Tạo 2 đối tượng cho 2 đầu đọc
MFRC522 mfrc522_1(RC522_1_SS_PIN, RC522_RST_PIN1);
MFRC522 mfrc522_2(RC522_2_SS_PIN, RC522_RST_PIN2);

void setupRFID() {

    pinMode(RC522_1_SS_PIN, OUTPUT);
    pinMode(RC522_2_SS_PIN, OUTPUT);
    digitalWrite(RC522_1_SS_PIN, HIGH); // deselect
    digitalWrite(RC522_2_SS_PIN, HIGH);
    // Quan trọng: Khởi tạo SPI với các chân HSPI tùy chỉnh của bạn
    SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN);
    
    // Khởi động cả 2 đầu đọc
    mfrc522_1.PCD_Init();
    mfrc522_2.PCD_Init();
    
    Serial.println("Da khoi tao 2 dau doc RFID (HSPI)");
    // In ra version để kiểm tra kết nối (nếu 0x00 hoặc 0xFF là lỗi dây)
    mfrc522_1.PCD_DumpVersionToSerial();
    mfrc522_2.PCD_DumpVersionToSerial();
}

String readUIDFromReader(MFRC522 &reader) {
    if (!reader.PICC_IsNewCardPresent() || !reader.PICC_ReadCardSerial()) {
        return "";
    }
    
    String uidString = "";
    for (byte i = 0; i < reader.uid.size; i++) {
        if (reader.uid.uidByte[i] < 0x10) uidString += "0";
        uidString += String(reader.uid.uidByte[i], HEX);
        if (i < reader.uid.size - 1) uidString += " ";
    }
    uidString.toUpperCase();
    
    // Dừng thẻ để đọc lại được
    reader.PICC_HaltA();
    reader.PCD_StopCrypto1();
    return uidString;
}

String getCardUID(int readerNum) {
    if (readerNum == 1) return readUIDFromReader(mfrc522_1);
    if (readerNum == 2) return readUIDFromReader(mfrc522_2);
    return "";
}