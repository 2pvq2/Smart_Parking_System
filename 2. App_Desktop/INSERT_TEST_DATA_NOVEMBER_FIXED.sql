-- ====================================================================
-- DỮ LIỆU ẢO CHO THÁNG 11/2024 - DÙNG DB BROWSER FOR SQLITE
-- ====================================================================
-- HƯỚNG DẪN SỬ DỤNG:
-- 1. Mở DB Browser for SQLite
-- 2. Mở file: parking_system.db
-- 3. Vào tab "Execute SQL"
-- 4. Copy và paste tất cả code dưới đây
-- 5. Click "Execute"
-- ====================================================================
-- SCHEMA parking_sessions (sau khi loại bỏ plate_out):
-- - id (auto), card_id, plate_in, time_in, time_out
-- - image_in_path, image_out_path, price, vehicle_type
-- - ticket_type, status, payment_method, slot_id
-- ====================================================================

-- NGÀY 1-5 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_001', '51F1234', '2024-11-01 07:30:00', '2024-11-01 08:45:00', 'Xe máy', 'M1', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_002', '51A5678', '2024-11-01 09:00:00', '2024-11-01 11:30:00', 'Ô tô', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_003', '29A1111', '2024-11-02 08:15:00', '2024-11-02 10:00:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_001', '51F2222', '2024-11-02 06:30:00', '2024-11-02 18:00:00', 'Xe máy', 'M3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_004', '30A3333', '2024-11-03 10:00:00', '2024-11-03 15:30:00', 'Ô tô', 'A2', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_005', '92K4444', '2024-11-03 14:00:00', '2024-11-03 16:15:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_002', '51C5555', '2024-11-04 07:00:00', '2024-11-04 19:00:00', 'Ô tô', 'A3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_006', '51F6666', '2024-11-04 11:30:00', '2024-11-04 13:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_007', '29A7777', '2024-11-05 09:00:00', '2024-11-05 12:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CASH', 'PAID');

-- NGÀY 6-10 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_008', '51A8888', '2024-11-06 08:00:00', '2024-11-06 09:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_003', '51F9999', '2024-11-06 07:30:00', '2024-11-06 17:30:00', 'Ô tó', 'A5', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_009', '30A0001', '2024-11-07 10:15:00', '2024-11-07 14:45:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_010', '92K0002', '2024-11-07 13:00:00', '2024-11-07 16:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_011', '51C0003', '2024-11-08 06:45:00', '2024-11-08 08:15:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_012', '51F0004', '2024-11-08 12:00:00', '2024-11-08 18:00:00', 'Ô tó', 'A2', 'GUEST', 35000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_004', '29A0005', '2024-11-09 07:00:00', '2024-11-09 19:00:00', 'Xe máy', 'M4', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_013', '51A0006', '2024-11-09 09:00:00', '2024-11-09 11:30:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_014', '30A0007', '2024-11-10 08:30:00', '2024-11-10 14:30:00', 'Ô tó', 'A3', 'GUEST', 25000, 'CASH', 'PAID');

-- NGÀY 11-15 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_015', '92K0008', '2024-11-11 07:15:00', '2024-11-11 09:00:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_016', '51C0009', '2024-11-11 11:00:00', '2024-11-11 15:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_005', '51F0010', '2024-11-12 06:30:00', '2024-11-12 18:30:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_017', '29A0011', '2024-11-12 09:00:00', '2024-11-12 12:30:00', 'Ô tó', 'A5', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_018', '51A0012', '2024-11-13 10:00:00', '2024-11-13 11:45:00', 'Xe máy', 'M3', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_019', '30A0013', '2024-11-13 13:00:00', '2024-11-13 18:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_020', '92K0014', '2024-11-14 08:00:00', '2024-11-14 10:00:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_006', '51C0015', '2024-11-14 07:00:00', '2024-11-14 19:00:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_021', '51F0016', '2024-11-15 14:00:00', '2024-11-15 17:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'ONLINE', 'PAID');

-- NGÀY 16-20 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_022', '29A0017', '2024-11-16 09:30:00', '2024-11-16 13:30:00', 'Ô tó', 'A3', 'GUEST', 35000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_023', '51A0018', '2024-11-16 07:00:00', '2024-11-16 08:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_024', '30A0019', '2024-11-17 10:00:00', '2024-11-17 16:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_007', '92K0020', '2024-11-17 06:00:00', '2024-11-17 18:00:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_025', '51C0021', '2024-11-18 08:15:00', '2024-11-18 10:45:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_026', '51F0022', '2024-11-18 12:00:00', '2024-11-18 17:00:00', 'Ô tó', 'A5', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_027', '29A0023', '2024-11-19 07:30:00', '2024-11-19 09:00:00', 'Xe máy', 'M4', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_028', '51A0024', '2024-11-19 11:00:00', '2024-11-19 15:30:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_008', '30A0025', '2024-11-20 06:30:00', '2024-11-20 18:30:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

-- NGÀY 21-25 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_029', '92K0026', '2024-11-21 09:00:00', '2024-11-21 11:30:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_030', '51C0027', '2024-11-21 13:00:00', '2024-11-21 18:00:00', 'Ô tó', 'A3', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_031', '51F0028', '2024-11-22 08:00:00', '2024-11-22 09:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_032', '29A0029', '2024-11-22 10:00:00', '2024-11-22 14:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_009', '51A0030', '2024-11-23 07:00:00', '2024-11-23 19:00:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_033', '30A0031', '2024-11-23 12:00:00', '2024-11-23 16:00:00', 'Ô tó', 'A5', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_034', '92K0032', '2024-11-24 07:30:00', '2024-11-24 09:00:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_035', '51C0033', '2024-11-24 11:00:00', '2024-11-24 15:30:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_036', '51F0034', '2024-11-25 09:00:00', '2024-11-25 10:30:00', 'Xe máy', 'M4', 'GUEST', 5000, 'ONLINE', 'PAID');

-- NGÀY 26-30 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_010', '29A0035', '2024-11-26 06:00:00', '2024-11-26 18:00:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_037', '51A0036', '2024-11-26 08:00:00', '2024-11-26 10:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_038', '30A0037', '2024-11-27 10:00:00', '2024-11-27 14:30:00', 'Ô tó', 'A3', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_039', '92K0038', '2024-11-27 07:00:00', '2024-11-27 08:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_040', '51C0039', '2024-11-28 12:00:00', '2024-11-28 17:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_041', '51F0040', '2024-11-28 09:30:00', '2024-11-28 11:00:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_011', '29A0041', '2024-11-29 07:30:00', '2024-11-29 18:30:00', 'Xe máy', 'M3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_042', '51A0042', '2024-11-29 11:00:00', '2024-11-29 13:30:00', 'Ô tó', 'A5', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_043', '30A0043', '2024-11-30 08:00:00', '2024-11-30 09:30:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_044', '92K0044', '2024-11-30 14:00:00', '2024-11-30 18:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CASH', 'PAID');

-- ====================================================================
-- TỔNG CỘNG: 44 GHI NHẬN CHO THÁNG 11
-- - 11 vé tháng (MONTHLY) với giá 0 VND
-- - 33 khách vãng lai (GUEST) với giá 5000-35000 VND
-- - 22 xe máy (Xe máy)
-- - 22 ô tó (Ô tó)
-- - Phân bố đều từ ngày 1-30 tháng 11/2024
-- ====================================================================

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_002', '51A5678', '51A5678', '2024-11-01 09:00:00', '2024-11-01 11:30:00', 'Ô tô', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_003', '29A1111', '29A1111', '2024-11-02 08:15:00', '2024-11-02 10:00:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_001', '51F2222', '51F2222', '2024-11-02 06:30:00', '2024-11-02 18:00:00', 'Xe máy', 'M3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_004', '30A3333', '30A3333', '2024-11-03 10:00:00', '2024-11-03 15:30:00', 'Ô tô', 'A2', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_005', '92K4444', '92K4444', '2024-11-03 14:00:00', '2024-11-03 16:15:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_002', '51C5555', '51C5555', '2024-11-04 07:00:00', '2024-11-04 19:00:00', 'Ô tô', 'A3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_006', '51F6666', '51F6666', '2024-11-04 11:30:00', '2024-11-04 13:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_007', '29A7777', '29A7777', '2024-11-05 09:00:00', '2024-11-05 12:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CASH', 'PAID');

-- NGÀY 6-10 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_008', '51A8888', '51A8888', '2024-11-06 08:00:00', '2024-11-06 09:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_003', '51F9999', '51F9999', '2024-11-06 07:30:00', '2024-11-06 17:30:00', 'Ô tó', 'A5', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_009', '30A0001', '30A0001', '2024-11-07 10:15:00', '2024-11-07 14:45:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_010', '92K0002', '92K0002', '2024-11-07 13:00:00', '2024-11-07 16:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_011', '51C0003', '51C0003', '2024-11-08 06:45:00', '2024-11-08 08:15:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_012', '51F0004', '51F0004', '2024-11-08 12:00:00', '2024-11-08 18:00:00', 'Ô tó', 'A2', 'GUEST', 35000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_004', '29A0005', '29A0005', '2024-11-09 07:00:00', '2024-11-09 19:00:00', 'Xe máy', 'M4', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_013', '51A0006', '51A0006', '2024-11-09 09:00:00', '2024-11-09 11:30:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_014', '30A0007', '30A0007', '2024-11-10 08:30:00', '2024-11-10 14:30:00', 'Ô tó', 'A3', 'GUEST', 25000, 'CASH', 'PAID');

-- NGÀY 11-15 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_015', '92K0008', '92K0008', '2024-11-11 07:15:00', '2024-11-11 09:00:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_016', '51C0009', '51C0009', '2024-11-11 11:00:00', '2024-11-11 15:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_005', '51F0010', '51F0010', '2024-11-12 06:30:00', '2024-11-12 18:30:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_017', '29A0011', '29A0011', '2024-11-12 09:00:00', '2024-11-12 12:30:00', 'Ô tó', 'A5', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_018', '51A0012', '51A0012', '2024-11-13 10:00:00', '2024-11-13 11:45:00', 'Xe máy', 'M3', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_019', '30A0013', '30A0013', '2024-11-13 13:00:00', '2024-11-13 18:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_020', '92K0014', '92K0014', '2024-11-14 08:00:00', '2024-11-14 10:00:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_006', '51C0015', '51C0015', '2024-11-14 07:00:00', '2024-11-14 19:00:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_021', '51F0016', '51F0016', '2024-11-15 14:00:00', '2024-11-15 17:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'ONLINE', 'PAID');

-- NGÀY 16-20 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_022', '29A0017', '29A0017', '2024-11-16 09:30:00', '2024-11-16 13:30:00', 'Ô tó', 'A3', 'GUEST', 35000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_023', '51A0018', '51A0018', '2024-11-16 07:00:00', '2024-11-16 08:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_024', '30A0019', '30A0019', '2024-11-17 10:00:00', '2024-11-17 16:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_007', '92K0020', '92K0020', '2024-11-17 06:00:00', '2024-11-17 18:00:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_025', '51C0021', '51C0021', '2024-11-18 08:15:00', '2024-11-18 10:45:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_026', '51F0022', '51F0022', '2024-11-18 12:00:00', '2024-11-18 17:00:00', 'Ô tó', 'A5', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_027', '29A0023', '29A0023', '2024-11-19 07:30:00', '2024-11-19 09:00:00', 'Xe máy', 'M4', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_028', '51A0024', '51A0024', '2024-11-19 11:00:00', '2024-11-19 15:30:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_008', '30A0025', '30A0025', '2024-11-20 06:30:00', '2024-11-20 18:30:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

-- NGÀY 21-25 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_029', '92K0026', '92K0026', '2024-11-21 09:00:00', '2024-11-21 11:30:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_030', '51C0027', '51C0027', '2024-11-21 13:00:00', '2024-11-21 18:00:00', 'Ô tó', 'A3', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_031', '51F0028', '51F0028', '2024-11-22 08:00:00', '2024-11-22 09:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_032', '29A0029', '29A0029', '2024-11-22 10:00:00', '2024-11-22 14:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_009', '51A0030', '51A0030', '2024-11-23 07:00:00', '2024-11-23 19:00:00', 'Xe máy', 'M2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_033', '30A0031', '30A0031', '2024-11-23 12:00:00', '2024-11-23 16:00:00', 'Ô tó', 'A5', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_034', '92K0032', '92K0032', '2024-11-24 07:30:00', '2024-11-24 09:00:00', 'Xe máy', 'M3', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_035', '51C0033', '51C0033', '2024-11-24 11:00:00', '2024-11-24 15:30:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_036', '51F0034', '51F0034', '2024-11-25 09:00:00', '2024-11-25 10:30:00', 'Xe máy', 'M4', 'GUEST', 5000, 'ONLINE', 'PAID');

-- NGÀY 26-30 THÁNG 11
INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_010', '29A0035', '29A0035', '2024-11-26 06:00:00', '2024-11-26 18:00:00', 'Ô tó', 'A2', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_037', '51A0036', '51A0036', '2024-11-26 08:00:00', '2024-11-26 10:00:00', 'Xe máy', 'M5', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_038', '30A0037', '30A0037', '2024-11-27 10:00:00', '2024-11-27 14:30:00', 'Ô tó', 'A3', 'GUEST', 25000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_039', '92K0038', '92K0038', '2024-11-27 07:00:00', '2024-11-27 08:30:00', 'Xe máy', 'M1', 'GUEST', 5000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_040', '51C0039', '51C0039', '2024-11-28 12:00:00', '2024-11-28 17:00:00', 'Ô tó', 'A4', 'GUEST', 25000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_041', '51F0040', '51F0040', '2024-11-28 09:30:00', '2024-11-28 11:00:00', 'Xe máy', 'M2', 'GUEST', 5000, 'CASH', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_MONTHLY_011', '29A0041', '29A0041', '2024-11-29 07:30:00', '2024-11-29 18:30:00', 'Xe máy', 'M3', 'MONTHLY', 0, 'FREE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_042', '51A0042', '51A0042', '2024-11-29 11:00:00', '2024-11-29 13:30:00', 'Ô tó', 'A5', 'GUEST', 25000, 'ONLINE', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_043', '30A0043', '30A0043', '2024-11-30 08:00:00', '2024-11-30 09:30:00', 'Xe máy', 'M4', 'GUEST', 5000, 'CARD', 'PAID');

INSERT INTO parking_sessions (card_id, plate_in, plate_out, time_in, time_out, vehicle_type, slot_id, ticket_type, price, payment_method, status) 
VALUES ('CARD_044', '92K0044', '92K0044', '2024-11-30 14:00:00', '2024-11-30 18:00:00', 'Ô tó', 'A1', 'GUEST', 25000, 'CASH', 'PAID');

-- ====================================================================
-- TỔNG CỘNG: 44 GHI NHẬN CHO THÁNG 11
-- - 11 vé tháng (MONTHLY) với giá 0 VND
-- - 33 khách vãng lai (GUEST) với giá 5000-35000 VND
-- - 22 xe máy (Xe máy)
-- - 22 ô tó (Ô tó)
-- - Phân bố đều từ ngày 1-30 tháng 11/2024
-- ====================================================================
