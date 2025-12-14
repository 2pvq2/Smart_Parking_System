#ifndef PIN_DEFINITIONS_H
#define PIN_DEFINITIONS_H

// --- SPI BUS (CHUNG CHO CẢ 2 ĐẦU ĐỌC) ---
// Lưu ý: Bạn đang dùng HSPI (14, 19, 13) thay vì VSPI mặc định
#define SPI_SCK_PIN   14
#define SPI_MISO_PIN  19
#define SPI_MOSI_PIN  13
#define RC522_RST_PIN1 16  // Chân Reset chung (hoặc dùng riêng cũng được)
#define RC522_RST_PIN2 4  // Chân Reset chung (hoặc dùng riêng cũng được)

// --- ĐẦU ĐỌC 1 (LÀN VÀO) ---
#define RC522_1_SS_PIN 5  

// --- ĐẦU ĐỌC 2 (LÀN RA) ---
#define RC522_2_SS_PIN 17 

// --- LÀN 1 (SERVO & BUZZER & CẢM BIẾN) ---
#define SERVO_1_PIN   32
#define BUZZER_1_PIN  25
#define IR_1_PIN      34  // Cảm biến làn 1

// --- LÀN 2 (SERVO & BUZZER & CẢM BIẾN) ---
#define SERVO_2_PIN   33
#define BUZZER_2_PIN  26
#define IR_2_PIN      35  // Cảm biến làn 2

// --- LCD I2C ---
#define LCD_SDA_PIN   21
#define LCD_SCL_PIN   22

#endif