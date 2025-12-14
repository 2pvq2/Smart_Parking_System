"""
Enhanced Card Scanned Handler với AI Integration
File này chứa logic xử lý hoàn chỉnh khi ESP32 gửi thẻ RFID
"""

import time
import os
from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

def handle_card_entry_with_ai(main_window, card_uid, lane):
    """
    Xử lý xe vào (Lane 1) với AI nhận diện biển số
    
    Flow:
    1. Nhận RFID từ ESP32
    2. Kiểm tra thẻ có hợp lệ không
    3. Chụp ảnh từ camera
    4. AI nhận diện biển số
    5. Lưu vào database
    6. Gửi lệnh mở barie
    7. Cập nhật LCD với thông tin
    
    Args:
        main_window: MainWindow instance
        card_uid (str): RFID UID
        lane (int): Lane number (should be 1)
    """
    print(f"\n{'='*60}")
    print(f"[ENTRY] XỬ LÝ XE VÀO - RFID: {card_uid}")
    print(f"{'='*60}")
    
    # Step 1: Kiểm tra thẻ trong database
    card_info = main_window.db.get_card_info(card_uid)
    
    if not card_info:
        print(f"[ENTRY] ❌ Thẻ không hợp lệ: {card_uid}")
        main_window.network_server.send_lcd_message("THE KHONG HOP LE", "Vui long lien he")
        main_window.network_server.send_command("REJECT_1")
        QMessageBox.warning(main_window, "Thẻ không hợp lệ", 
                          f"Thẻ {card_uid} không có trong hệ thống!")
        return
    
    print(f"[ENTRY] ✅ Thẻ hợp lệ: {card_info.get('owner_name', 'Unknown')}")
    
    # Step 2: Gửi LCD thông báo đang xử lý
    main_window.network_server.send_lcd_message("DANG XU LY...", f"The: {card_uid[:12]}")
    
    # Step 3: Chụp ảnh từ camera
    print("[ENTRY] 📷 Đang chụp ảnh từ camera...")
    frame = None
    
    if main_window.camera_entry_thread and main_window.camera_entry_thread.isRunning():
        # Get latest frame from camera thread
        frame = main_window.camera_entry_thread.get_latest_frame()
        
        if frame is not None and frame.size > 0:
            print(f"[ENTRY] ✅ Đã chụp ảnh ({frame.shape})")
            
            # Lưu ảnh vào thư mục reports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"entry_{card_uid}_{timestamp}.jpg"
            image_dir = os.path.join(os.path.dirname(__file__), "..", "reports", "images")
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, image_filename)
            
            import cv2
            cv2.imwrite(image_path, frame)
            print(f"[ENTRY] 💾 Lưu ảnh: {image_path}")
        else:
            print("[ENTRY] ⚠️ Không thể lấy frame từ camera")
            frame = None
    else:
        print("[ENTRY] ⚠️ Camera thread chưa khởi động")
    
    # Step 4: AI nhận diện biển số
    license_plate = None
    
    if frame is not None:
        try:
            from core.lpr_wrapper import get_lpr_instance
            lpr = get_lpr_instance(enable_ai=True)
            
            if lpr.is_enabled():
                print("[ENTRY] 🤖 Đang nhận diện biển số bằng AI...")
                license_plate = lpr.process_frame(frame, save_debug=True)
                
                if license_plate:
                    print(f"[ENTRY] ✅ AI nhận diện: {license_plate}")
                else:
                    print("[ENTRY] ⚠️ AI không phát hiện biển số")
            else:
                print("[ENTRY] ⚠️ AI module không khả dụng")
        except Exception as e:
            print(f"[ENTRY] ❌ Lỗi AI: {e}")
            license_plate = None
    
    # Step 5: Nếu AI không phát hiện, cho phép nhập thủ công
    if not license_plate:
        license_plate = "UNKNOWN"
        print("[ENTRY] 📝 Biển số chưa xác định - cần nhập thủ công")
        # Có thể hiển thị dialog để nhập thủ công nếu cần
    
    # Step 6: Lưu vào database
    print("[ENTRY] 💾 Đang lưu vào database...")
    
    vehicle_type = card_info.get('vehicle_type', 'Ô tô')
    time_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        record_id = main_window.db.execute("""
            INSERT INTO parking_records 
            (card_uid, license_plate, vehicle_type, time_in, lane_in, image_in, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PARKED')
        """, (card_uid, license_plate, vehicle_type, time_in, lane, image_path if frame else None))
        
        print(f"[ENTRY] ✅ Đã lưu record ID: {record_id}")
        
        # Cập nhật số chỗ trống
        main_window.send_slot_info_to_esp()
        
    except Exception as e:
        print(f"[ENTRY] ❌ Lỗi lưu database: {e}")
        main_window.network_server.send_lcd_message("LOI HE THONG", "Vui long thu lai")
        return
    
    # Step 7: Gửi lệnh mở barie
    print("[ENTRY] 🚪 Gửi lệnh mở barie...")
    main_window.network_server.open_barrier(1)
    
    # Step 8: Cập nhật LCD với thông tin chi tiết
    owner_name = card_info.get('owner_name', 'KHACH')
    lcd_line1 = f"{license_plate[:16]}"  # Max 16 chars
    lcd_line2 = f"{owner_name[:16]}"
    
    main_window.network_server.send_lcd_message(lcd_line1, lcd_line2)
    
    # Step 9: Cập nhật UI
    if hasattr(main_window, 'txt_entry_rfid'):
        main_window.txt_entry_rfid.setText(card_uid)
    
    if hasattr(main_window, 'lbl_entry_plate_detected'):
        main_window.lbl_entry_plate_detected.setText(license_plate)
    
    if hasattr(main_window, 'lbl_entry_guidance'):
        main_window.lbl_entry_guidance.setText(
            f"✅ Xe vào: {license_plate} | {owner_name}"
        )
        main_window.lbl_entry_guidance.setStyleSheet("color: #22c55e; font-weight: bold;")
    
    print(f"[ENTRY] ✅ HOÀN TẤT - Chờ xe đi vào...")
    print(f"{'='*60}\n")


def handle_card_exit_with_ai(main_window, card_uid, lane):
    """
    Xử lý xe ra (Lane 2) với AI và tính phí
    
    Flow:
    1. Nhận RFID từ ESP32 (hoặc không có thẻ)
    2. Chụp ảnh từ camera
    3. AI nhận diện biển số
    4. Tìm xe trong database (theo thẻ hoặc biển số)
    5. Tính phí đỗ xe
    6. Hiển thị dialog thanh toán
    7. Sau khi xác nhận -> Gửi lệnh mở barie
    8. Cập nhật database
    
    Args:
        main_window: MainWindow instance
        card_uid (str): RFID UID (có thể rỗng nếu không quét thẻ)
        lane (int): Lane number (should be 2)
    """
    print(f"\n{'='*60}")
    print(f"[EXIT] XỬ LÝ XE RA - RFID: {card_uid if card_uid else 'KHÔNG CÓ THẺ'}")
    print(f"{'='*60}")
    
    # Step 1: Gửi LCD thông báo
    main_window.network_server.send_lcd_message("DANG XU LY...", "Vui long doi")
    
    # Step 2: Chụp ảnh từ camera
    print("[EXIT] 📷 Đang chụp ảnh từ camera...")
    frame = None
    
    if main_window.camera_exit_thread and main_window.camera_exit_thread.isRunning():
        frame = main_window.camera_exit_thread.get_latest_frame()
        
        if frame is not None and frame.size > 0:
            print(f"[EXIT] ✅ Đã chụp ảnh ({frame.shape})")
            
            # Lưu ảnh
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"exit_{card_uid if card_uid else 'nocard'}_{timestamp}.jpg"
            image_dir = os.path.join(os.path.dirname(__file__), "..", "reports", "images")
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, image_filename)
            
            import cv2
            cv2.imwrite(image_path, frame)
            print(f"[EXIT] 💾 Lưu ảnh: {image_path}")
        else:
            print("[EXIT] ⚠️ Không thể lấy frame từ camera")
            frame = None
    
    # Step 3: AI nhận diện biển số
    license_plate = None
    
    if frame is not None:
        try:
            from core.lpr_wrapper import get_lpr_instance
            lpr = get_lpr_instance(enable_ai=True)
            
            if lpr.is_enabled():
                print("[EXIT] 🤖 Đang nhận diện biển số bằng AI...")
                license_plate = lpr.process_frame(frame, save_debug=True)
                
                if license_plate:
                    print(f"[EXIT] ✅ AI nhận diện: {license_plate}")
                else:
                    print("[EXIT] ⚠️ AI không phát hiện biển số")
        except Exception as e:
            print(f"[EXIT] ❌ Lỗi AI: {e}")
    
    # Step 4: Tìm xe trong bãi
    vehicle = None
    
    if card_uid:
        # Tìm theo RFID
        vehicle = main_window.db.query("""
            SELECT * FROM parking_records 
            WHERE card_uid = ? AND status = 'PARKED'
            ORDER BY time_in DESC LIMIT 1
        """, (card_uid,))
    
    if not vehicle and license_plate:
        # Tìm theo biển số
        vehicle = main_window.db.query("""
            SELECT * FROM parking_records 
            WHERE license_plate = ? AND status = 'PARKED'
            ORDER BY time_in DESC LIMIT 1
        """, (license_plate,))
    
    if not vehicle:
        print("[EXIT] ❌ Không tìm thấy xe trong bãi")
        main_window.network_server.send_lcd_message("KHONG TIM THAY", "Vui long lien he")
        QMessageBox.warning(main_window, "Không tìm thấy", 
                          "Không tìm thấy xe trong hệ thống!")
        return
    
    print(f"[EXIT] ✅ Tìm thấy xe: {vehicle.get('license_plate')}")
    
    # Step 5: Tính phí
    time_in_str = vehicle.get('time_in')
    time_out = time.time()
    vehicle_type = vehicle.get('vehicle_type', 'Ô tô')
    
    try:
        from main import calculate_parking_fee
        fee = calculate_parking_fee(main_window.db, vehicle_type, time_in_str, time_out)
        print(f"[EXIT] 💰 Phí đỗ xe: {fee:,} VND")
    except Exception as e:
        print(f"[EXIT] ❌ Lỗi tính phí: {e}")
        fee = 0
    
    # Step 6: Hiển thị LCD phí
    main_window.network_server.send_lcd_message(
        f"PHI: {fee//1000}K VND",
        "Vui long thanh toan"
    )
    
    # Step 7: Hiển thị dialog thanh toán (import từ main.py)
    from main import PaymentDialog
    dialog = PaymentDialog(fee, main_window)
    
    if dialog.exec() == PaymentDialog.Accepted:
        print(f"[EXIT] ✅ Thanh toán thành công - Phương thức: {dialog.payment_method}")
        
        # Step 8: Cập nhật database
        time_out_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration_minutes = (time_out - time.mktime(time.strptime(time_in_str, "%Y-%m-%d %H:%M:%S"))) / 60
        
        main_window.db.execute("""
            UPDATE parking_records 
            SET time_out = ?, duration_minutes = ?, fee = ?, 
                lane_out = ?, image_out = ?, status = 'CHECKED_OUT',
                payment_method = ?
            WHERE id = ?
        """, (time_out_str, duration_minutes, fee, lane, 
              image_path if frame else None, dialog.payment_method, vehicle.get('id')))
        
        print(f"[EXIT] 💾 Đã cập nhật database")
        
        # Step 9: Gửi lệnh mở barie
        print("[EXIT] 🚪 Gửi lệnh mở barie...")
        main_window.network_server.open_barrier(2)
        
        # Step 10: Cập nhật LCD
        main_window.network_server.send_lcd_message(
            "TAM BIET!",
            f"{vehicle.get('license_plate', '')[:16]}"
        )
        
        # Step 11: Cập nhật slot info
        main_window.send_slot_info_to_esp()
        
        # Step 12: Cập nhật UI
        if hasattr(main_window, 'lbl_exit_guidance'):
            main_window.lbl_exit_guidance.setText(
                f"✅ Xe ra: {vehicle.get('license_plate')} | Phí: {fee:,} VND"
            )
            main_window.lbl_exit_guidance.setStyleSheet("color: #22c55e; font-weight: bold;")
        
        print(f"[EXIT] ✅ HOÀN TẤT")
    else:
        print("[EXIT] ❌ Người dùng hủy thanh toán")
        main_window.network_server.send_lcd_message("DA HUY", "Vui long thu lai")
    
    print(f"{'='*60}\n")


def enhanced_card_scanned_handler(main_window, card_uid, lane):
    """
    Main handler được gọi từ main.py khi nhận signal card_scanned
    
    Usage in main.py:
        from enhanced_handler import enhanced_card_scanned_handler
        self.network_server.card_scanned.connect(
            lambda uid, ln: enhanced_card_scanned_handler(self, uid, ln)
        )
    """
    try:
        if lane == 1:
            # Xe vào
            handle_card_entry_with_ai(main_window, card_uid, lane)
        elif lane == 2:
            # Xe ra
            handle_card_exit_with_ai(main_window, card_uid, lane)
        else:
            print(f"[ERROR] Lane không hợp lệ: {lane}")
    
    except Exception as e:
        print(f"[ERROR] Lỗi xử lý thẻ: {e}")
        import traceback
        traceback.print_exc()
        
        # Gửi thông báo lỗi lên LCD
        if hasattr(main_window, 'network_server'):
            main_window.network_server.send_lcd_message("LOI HE THONG", "Lien he quan ly")
