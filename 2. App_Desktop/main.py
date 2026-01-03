#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
                               QStackedWidget, QTableWidget, QTableWidgetItem, QLineEdit, 
                               QComboBox, QDateEdit, QFileDialog, QMessageBox, QGraphicsView, QGraphicsScene,
                               QProgressBar, QDialog, QVBoxLayout, QHBoxLayout, QTimeEdit, QSpinBox, QCheckBox, QFrame,
                               QHeaderView, QScrollArea)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDate, QTime, Qt, QRectF, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor, QBrush, QPen, QFont
import PIL.Image

# --- CẤU HÌNH IMPORT THEO CẤU TRÚC MỚI ---
# Thêm thư mục hiện tại (2. App_Desktop) vào sys.path để import các file ngang cấp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import UI_PATH, PAGES_PATH, CAMERA_ENTRY_ID, CAMERA_EXIT_ID, ENABLE_AI_DETECTION
from database import init_db, migrate_db # Import functions to initialize and update DB
from core.db_manager import DBManager
from core.camera_thread import CameraThread
from core.network_server import NetworkServer
from core.sensor_manager import SensorDataManager
from login_dialog import LoginDialog

# --- CẤU HÌNH CHUNG CÓ THỂ THAY ĐỔI ---
MOTOR_SLOTS = 5  # Số slot xe máy
CAR_SLOTS = 5    # Số slot ô tô

# --- TÍNH PHÍ (Hàm độc lập) ---
# Tái định nghĩa hàm tính phí vì nó sử dụng DBManager (cần giữ logic này trong main)
def calculate_parking_fee(db: DBManager, vehicle_type: str, time_in_str: str, time_out_seconds: float):
    # Tính phí dựa trên bảng giá từ settings
    try:
        time_in = time.mktime(time.strptime(time_in_str, "%Y-%m-%d %H:%M:%S"))
        parking_duration_minutes = (time_out_seconds - time_in) / 60
        
        if parking_duration_minutes < 0: return 0
        
        # Lấy giá từ settings
        price_key_1 = f"price_{vehicle_type.lower().replace(' ', '_')}_block1"
        price_key_2 = f"price_{vehicle_type.lower().replace(' ', '_')}_block2"
        
        price_block1 = int(db.get_setting(price_key_1, '5000'))    # Giá lần đầu
        price_block2 = int(db.get_setting(price_key_2, '3000'))    # Giá mỗi giờ tiếp theo
        
        # Block 1: 120 phút đầu (2 giờ) tính lần đầu
        # Sau đó tính thêm VÀO (không phải thay thế)
        block1_minutes = 120
        fee = 0
        
        if parking_duration_minutes <= block1_minutes:
            # Nếu ≤ 2h, chỉ tính lần đầu
            fee = price_block1
        else:
            # Nếu > 2h, tính lần đầu + thêm giờ
            fee = price_block1
            remaining_minutes = parking_duration_minutes - block1_minutes
            extra_blocks = int(remaining_minutes / 60)
            if remaining_minutes % 60 > 0:
                extra_blocks += 1
            
            fee += extra_blocks * price_block2
            
        return round(fee / 1000) * 1000 
    except Exception as e:
        print(f"Lỗi tính phí: {e}")
        return 0
# -----------------------------

# --- CLICKABLE LABEL CLASS ---
class ClickableLabel(QLabel):
    """Custom QLabel cho phép click để phóng to ảnh"""
    clicked = None  # Signal placeholder
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.callback = None
        self.setCursor(Qt.PointingHandCursor)
    
    def set_click_callback(self, callback):
        """Đặt callback khi click"""
        self.callback = callback
    
    def mousePressEvent(self, event):
        """Xử lý sự kiện click chuột"""
        if self.callback:
            self.callback()
        super().mousePressEvent(event)

# --- DIALOG THANH TOÁN ---
class PaymentDialog(QDialog):
    def __init__(self, plate, vehicle_type, amount, parent=None):
        super().__init__(parent)
        self.plate = plate
        self.vehicle_type = vehicle_type
        self.amount = amount
        self.payment_method = "CASH"
        self.payment_confirmed = False
        
        self.setWindowTitle("💳 Thanh toán")
        self.setMinimumSize(500, 600)
        
        # Tạo UI trực tiếp
        self.setup_ui()
    
    def setup_ui(self):
        """Thiết lập giao diện thanh toán"""
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        lbl_title = QLabel("💳 THANH TOÁN")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(lbl_title)
        
        # Thông tin
        icon = "🏍️" if self.vehicle_type == "Xe máy" else "🚗"
        lbl_plate = QLabel(f"Biển số: {self.plate}")
        lbl_plate.setAlignment(Qt.AlignCenter)
        lbl_plate.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl_plate)
        
        lbl_vehicle = QLabel(f"Loại xe: {icon} {self.vehicle_type}")
        lbl_vehicle.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_vehicle)
        
        # Số tiền
        lbl_amount = QLabel(f"Số tiền: {self.amount:,} VND")
        lbl_amount.setAlignment(Qt.AlignCenter)
        lbl_amount.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff6b6b; padding: 15px;")
        layout.addWidget(lbl_amount)
        
        # Phương thức thanh toán
        lbl_method = QLabel("Phương thức thanh toán:")
        lbl_method.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_method)
        
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["💵 Tiền mặt", "🏦 Chuyển khoản", "📱 QR Code"])
        self.cmb_method.currentIndexChanged.connect(self.on_payment_method_changed)
        layout.addWidget(self.cmb_method)
        
        # Stacked widget cho các phương thức
        self.stacked = QStackedWidget()
        
        # Page 0: Tiền mặt
        page_cash = QWidget()
        cash_layout = QVBoxLayout(page_cash)
        lbl_cash = QLabel("✅ Nhân viên xác nhận đã nhận tiền mặt")
        lbl_cash.setAlignment(Qt.AlignCenter)
        lbl_cash.setWordWrap(True)
        lbl_cash.setStyleSheet("padding: 20px;")
        cash_layout.addWidget(lbl_cash)
        cash_layout.addStretch()
        self.stacked.addWidget(page_cash)
        
        # Page 1: Chuyển khoản
        page_transfer = QWidget()
        transfer_layout = QVBoxLayout(page_transfer)
        lbl_bank = QLabel(f"""🏦 Thông tin chuyển khoản:

Ngân hàng: VCB - Vietcombank
Số tài khoản: 1234567890
Chủ TK: CONG TY BAI DO XE
Số tiền: {self.amount:,} VND
Nội dung: {self.plate}

⚠️ Vui lòng chuyển khoản và đợi nhân viên xác nhận""")
        lbl_bank.setWordWrap(True)
        lbl_bank.setStyleSheet("padding: 15px; background: #f8f9fa; border-radius: 5px;")
        transfer_layout.addWidget(lbl_bank)
        transfer_layout.addStretch()
        self.stacked.addWidget(page_transfer)
        
        # Page 2: QR Code
        page_qr = QWidget()
        qr_layout = QVBoxLayout(page_qr)
        lbl_qr = QLabel("📱 Quét mã QR để thanh toán\n\n(Tính năng sẽ được bổ sung)")
        lbl_qr.setAlignment(Qt.AlignCenter)
        lbl_qr.setWordWrap(True)
        lbl_qr.setStyleSheet("padding: 20px;")
        qr_layout.addWidget(lbl_qr)
        qr_layout.addStretch()
        self.stacked.addWidget(page_qr)
        
        layout.addWidget(self.stacked)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("❌ Hủy")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_confirm = QPushButton("✅ Xác nhận thanh toán")
        btn_confirm.setMinimumHeight(40)
        btn_confirm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_confirm.clicked.connect(self.confirm_payment)
        btn_layout.addWidget(btn_confirm)
        
        layout.addLayout(btn_layout)
    
    def on_payment_method_changed(self, index):
        """Xử lý khi đổi phương thức thanh toán"""
        methods = ["CASH", "TRANSFER", "QR"]
        self.payment_method = methods[index]
        self.stacked.setCurrentIndex(index)  # Thay đổi trang hiển thị
        print(f"[Payment] Method changed to: {self.payment_method}")
    
    def confirm_payment(self):
        """Xác nhận thanh toán"""
        reply = QMessageBox.question(self, "Xác nhận", 
            f"Xác nhận đã nhận thanh toán {self.amount:,} VND bằng {self.payment_method}?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.payment_confirmed = True
            self.accept()
# -----------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Khởi tạo DB Manager
        self.db = DBManager()
        self.camera_entry_thread = None
        self.camera_exit_thread = None
        
        # Khởi tạo Sensor Data Manager
        self.sensor_manager = SensorDataManager(self.db)
        self.sensor_manager.set_vehicle_type("Tổng hợp")  # 10 slots cho cả xe máy & ô tô
        self.sensor_manager.set_vehicle_type("Xe máy")  # Mặc định zone cảm biến cho xe máy
        self.sensor_manager.slots_changed.connect(self.on_sensor_slots_changed, Qt.QueuedConnection)
        print("[INIT] ✅ Sensor Manager initialized")
        
        # Timer tự động refresh dashboard mỗi 2 giây
        self.dashboard_refresh_timer = QTimer(self)
        self.dashboard_refresh_timer.timeout.connect(self.auto_refresh_dashboard)
        self.dashboard_refresh_timer.start(2000)  # 2000ms = 2 giây
        print("[INIT] ✅ Auto-refresh timer started (2s interval)")
        
        # Khởi tạo Network Server (kết nối với ESP32)
        self.network_server = NetworkServer(host='0.0.0.0', port=8888)
        # Sử dụng Qt.QueuedConnection cho cross-thread signal
        self.network_server.card_scanned.connect(self.on_esp_card_scanned, Qt.QueuedConnection)
        self.network_server.barrier_closed.connect(self.on_barrier_closed, Qt.QueuedConnection)
        self.network_server.esp_connected.connect(self.on_esp_connected, Qt.QueuedConnection)
        self.network_server.esp_disconnected.connect(self.on_esp_disconnected, Qt.QueuedConnection)
        self.network_server.sensor_data_received.connect(self.on_sensor_data_received, Qt.QueuedConnection)
        print("[INIT] ✅ Network signals connected with QueuedConnection")
        self.network_server.start()
        
        # Biến trạng thái giao dịch
        self.current_entry_plate = "..."
        self.current_entry_card = "" 
        self.current_exit_plate = "..."
        self.current_entry_vehicle_type = "Ô tô"  # Mặc định
        self.parking_map_scene = None  # Khởi tạo sớm để tránh lỗi
        
        # Tracking để tránh update UI không cần thiết
        self._last_sensor_binary = None
        self._last_sensor_binary_time = 0  # Track thời gian binary cuối cùng được update
        
        # Timer để gửi LCD idle message định kỳ (TẠM TẮT ĐỂ DEBUG)
        # from PySide6.QtCore import QTimer
        # self.lcd_idle_timer = QTimer()
        # self.lcd_idle_timer.timeout.connect(self.send_idle_lcd_message)
        # self.lcd_idle_timer.start(30000)  # Mỗi 30 giây
        
        # 1. Load giao diện chính
        # Giả định file chính app_mainwindow.ui nằm trong 2. App_Desktop/ui
        self.ui = self.load_ui_file(os.path.join(UI_PATH, "app_mainwindow.ui"))
        if self.ui:
            # Dùng setCentralWidget(self.ui) nếu app_mainwindow.ui là QWidget, 
            # hoặc self.setCentralWidget(self.ui.centralWidget()) nếu là QMainWindow
            self.setCentralWidget(self.ui) 
            
        self.setWindowTitle(self.db.get_setting("parking_name", "Hệ thống giữ xe"))
        self.resize(1280, 800)

        # 2. Setup các trang con (Pages)
        self.setup_pages()

        # 3. Setup Menu bên trái (Sidebar)
        # Vì self.ui là QMainWindow, ta cần tìm các widget qua self.ui
        self.setup_sidebar()

        # 4. Load cấu hình ban đầu
        self.load_initial_settings()
        
        # 5. Khởi động Camera
        self.start_cameras()
        
        # ⚡ 6. PRE-LOAD AI ở background (không block UI)
        self.preload_ai_background()

    def preload_ai_background(self):
        """⚡ Pre-load AI model ở background thread sau khi app khởi động
        
        Lợi ích:
        - Startup UI nhanh (không chờ AI)
        - Tải AI ở background (user thấy UI trong khi đợi)
        - Chụp lần 1: instant (AI đã sẵn sàng)
        """
        from PySide6.QtCore import QThread
        
        def load_ai_in_background():
            """Tải AI trong thread riêng"""
            print("[AI PRELOAD] ⚡ Bắt đầu tải AI ở background...")
            try:
                # Đảm bảo camera threads được tạo trước
                if self.camera_entry_thread:
                    print("[AI PRELOAD] 📹 Entry camera - Đang tải AI...")
                    self.camera_entry_thread._ensure_lpr_loaded()
                    print("[AI PRELOAD] ✅ Entry camera - AI tải xong")
                
                if self.camera_exit_thread:
                    print("[AI PRELOAD] 📹 Exit camera - Đang tải AI...")
                    self.camera_exit_thread._ensure_lpr_loaded()
                    print("[AI PRELOAD] ✅ Exit camera - AI tải xong")
                
                print("[AI PRELOAD] ✅ Tất cả AI đã sẵn sàng!")
            except Exception as e:
                print(f"[AI PRELOAD] ❌ Lỗi tải AI: {e}")
        
        # Chạy trong QTimer (sau 1s cho UI render xong)
        QTimer.singleShot(1000, lambda: load_ai_in_background())

    def load_ui_file(self, path):
        loader = QUiLoader()
        file = QFile(path)
        if not file.open(QFile.ReadOnly):
            print(f"Lỗi: Không thể mở file UI: {path}")
            return None
        widget = loader.load(file)
        file.close()
        return widget
        
    def setup_pages(self):
        # Tìm QStackedWidget trong giao diện chính
        self.stacked_widget = self.ui.findChild(QStackedWidget, "stackedPages")
        
        if not self.stacked_widget: return
        self.pages = {
            "dashboard": "dashboard.ui", "monthly": "monthly.ui",
            "history": "history.ui", "parking_map": "parking_map.ui", "statistics": "statistics.ui", "settings": "settings.ui"
        }
        self.loaded_pages = {} 
        for key, filename in self.pages.items():
            page_path = os.path.join(PAGES_PATH, filename)
            if os.path.exists(page_path):
                page_widget = self.load_ui_file(page_path)
                if page_widget:
                    self.stacked_widget.addWidget(page_widget)
                    self.loaded_pages[key] = page_widget
                    if key == "monthly":
                        self.setup_monthly_page(page_widget)
                    elif key == "dashboard":
                        self.setup_dashboard_page(page_widget)
                    elif key == "history":
                        self.setup_history_page(page_widget)
                    elif key == "parking_map":
                        self.setup_parking_map_page(page_widget)
                    elif key == "statistics":
                        self.setup_statistics_page(page_widget)
                    elif key == "settings":
                        self.setup_settings_page(page_widget)
        if "dashboard" in self.loaded_pages:
            self.stacked_widget.setCurrentWidget(self.loaded_pages["dashboard"])

    def setup_sidebar(self):
        buttons = { "btnDashboard": "dashboard", "btnMonthly": "monthly",
                    "btnHistory": "history", "btnParkingMap": "parking_map", "btnStatistics": "statistics", "btnSettings": "settings" }
        for btn_name, page_key in buttons.items():
            btn = self.ui.findChild(QPushButton, btn_name)
            if btn:
                btn.clicked.connect(lambda checked, k=page_key: self.switch_page(k))

    def switch_page(self, page_key):
        if page_key in self.loaded_pages:
            self.stacked_widget.setCurrentWidget(self.loaded_pages[page_key])
            self.update_active_button(page_key)
            if page_key == "monthly":
                self.load_monthly_tickets()
            elif page_key == "dashboard":
                self.draw_parking_map() # Refresh sơ đồ
                self.update_dashboard_stats()  # Refresh thống kê
            elif page_key == "history":
                self.load_history()  # Load lịch sử
            elif page_key == "parking_map":
                self.update_parking_map_realtime()  # Refresh realtime parking map

    def update_active_button(self, active_key):
        buttons_map = { "dashboard": "btnDashboard", "monthly": "btnMonthly",
                        "history": "btnHistory", "parking_map": "btnParkingMap", "statistics": "btnStatistics", "settings": "btnSettings" }
        for key, btn_name in buttons_map.items():
            btn = self.ui.findChild(QPushButton, btn_name)
            if btn:
                btn.setProperty("active", str(key == active_key).lower())
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                
    # --- LOGIC TRANG DASHBOARD ---
    
    def setup_dashboard_page(self, widget):
        # Cổng vào (Entry) - sử dụng tên widget từ dashboard.ui
        self.lbl_entry_plate = widget.findChild(QLabel, "latestEntry_plate")
        self.lbl_entry_slot = widget.findChild(QLabel, "latestEntry_slot")
        self.lbl_entry_time = widget.findChild(QLabel, "latestEntry_time")
        self.lbl_entry_guidance = widget.findChild(QLabel, "lbl_entry_guidance")
        self.txt_entry_rfid = widget.findChild(QLineEdit, "txt_entry_rfid")
        
        # Cổng ra (Exit)
        self.lbl_exit_plate = widget.findChild(QLabel, "latestExit_plate")
        self.lbl_exit_slot = widget.findChild(QLabel, "latestExit_slot")
        self.lbl_exit_time_price = widget.findChild(QLabel, "latestExit_time_price")
        self.lbl_exit_fee = widget.findChild(QLabel, "lbl_exit_fee")
        self.txt_exit_rfid = widget.findChild(QLineEdit, "txt_exit_rfid")  # RFID cho cổng ra
        print(f"[DEBUG] txt_exit_rfid found: {self.txt_exit_rfid is not None}")
        
        # Thống kê số liệu
        self.lbl_stat1_value = widget.findChild(QLabel, "stat1_value")  # Xe máy đang gửi
        self.lbl_stat2_value = widget.findChild(QLabel, "stat2_value")  # Ô tô đang gửi
        self.lbl_stat3_value = widget.findChild(QLabel, "stat3_value")  # Xe đã vào
        self.lbl_stat4_value = widget.findChild(QLabel, "stat4_value")  # Xe đã ra
        
        # Chỗ trống
        self.lbl_avail1_value = widget.findChild(QLabel, "avail1_value")
        self.lbl_avail1_progress = widget.findChild(QProgressBar, "avail1_progress")
        self.lbl_avail2_value = widget.findChild(QLabel, "avail2_value")
        self.lbl_avail2_progress = widget.findChild(QProgressBar, "avail2_progress")
        
        # Buttons barie và thanh toán
        self.btn_open_barrier_in = widget.findChild(QPushButton, "btnOpenBarrierIn")
        self.btn_open_barrier_out = widget.findChild(QPushButton, "btnOpenBarrierOut")
        self.btn_confirm_exit = widget.findChild(QPushButton, "btnConfirmExit")
        
        # Kết nối sự kiện RFID
        if self.txt_entry_rfid:
            self.txt_entry_rfid.returnPressed.connect(self.handle_rfid_scan)
            # Thêm button test camera (tạm thời để debug)
            self.txt_entry_rfid.textChanged.connect(self.on_rfid_text_changed)
        if self.txt_exit_rfid:
            self.txt_exit_rfid.returnPressed.connect(self.handle_exit_rfid_scan)
        
        # Kết nối nút barie (nếu cần)
        if self.btn_open_barrier_in:
            self.btn_open_barrier_in.clicked.connect(self.handle_open_barrier_in)
        if self.btn_open_barrier_out:
            self.btn_open_barrier_out.clicked.connect(self.handle_open_barrier_out)
        if self.btn_confirm_exit:
            self.btn_confirm_exit.clicked.connect(self.handle_confirm_exit)
        
        # 🖼️ Kết nối chức năng click phóng to ảnh vào/ra
        cam_entry = widget.findChild(QLabel, "camEntryImage")
        cam_exit = widget.findChild(QLabel, "camExitImage")
        
        if cam_entry:
            cam_entry.setCursor(Qt.PointingHandCursor)
            # Lưu reference để sử dụng trong method
            self.cam_entry_label = cam_entry
            # Sử dụng installEventFilter để bắt event click
            cam_entry.installEventFilter(self)
        
        if cam_exit:
            cam_exit.setCursor(Qt.PointingHandCursor)
            self.cam_exit_label = cam_exit
            cam_exit.installEventFilter(self)

        # Sơ đồ bãi đỗ xe (Parking Map)
        parking_map_view = widget.findChild(QGraphicsView, "parkingMapView")
        if parking_map_view:
            self.parking_map_scene = QGraphicsScene()
            parking_map_view.setScene(self.parking_map_scene)
            self.draw_parking_map() # Vẽ sơ đồ lần đầu
        
        # Tải thông tin vào/ra cuối cùng từ DB để hiển thị persistent
        self.load_last_entry_exit_info()
        
        # Cập nhật thống kê ban đầu
        self.update_dashboard_stats()
    
    def show_image_fullscreen(self, label, title):
        """Hiển thị ảnh phóng to trong dialog khi click vào ảnh"""
        pixmap = label.pixmap()
        
        if not pixmap or pixmap.isNull():
            QMessageBox.warning(self, "Chưa có ảnh", f"{title} chưa có dữ liệu")
            return
        
        # Tạo dialog để hiển thị ảnh
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🖼️ {title}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Label hiển thị ảnh phóng to
        lbl_image = QLabel()
        scaled_pixmap = pixmap.scaledToWidth(750, Qt.SmoothTransformation)
        lbl_image.setPixmap(scaled_pixmap)
        lbl_image.setAlignment(Qt.AlignCenter)
        
        # Scroll area để xem ảnh lớn
        scroll = QScrollArea()
        scroll.setWidget(lbl_image)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Nút đóng
        btn_close = QPushButton("Đóng (ESC)")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec()
    
    def eventFilter(self, obj, event):
        """Xử lý sự kiện click trên ảnh vào/ra"""
        from PySide6.QtCore import QEvent
        
        # Kiểm tra nếu là event click trên camEntryImage hoặc camExitImage
        if event.type() == QEvent.MouseButtonRelease:
            if hasattr(self, 'cam_entry_label') and obj == self.cam_entry_label:
                self.show_image_fullscreen(self.cam_entry_label, "Ảnh cổng vào")
                return True
            elif hasattr(self, 'cam_exit_label') and obj == self.cam_exit_label:
                self.show_image_fullscreen(self.cam_exit_label, "Ảnh cổng ra")
                return True
        
        return super().eventFilter(obj, event)

    def draw_parking_map(self):
        if not hasattr(self, 'parking_map_scene') or not self.parking_map_scene: 
            return
        self.parking_map_scene.clear()
        
        slots = self.db.get_all_parking_slots()
        
        slot_width = 120
        slot_height = 50
        spacing = 10
        cols = 2
        
        font = QFont("Arial", 10)
        max_height = 0

        for i, slot in enumerate(slots):
            slot_id = slot[0] # Lấy dữ liệu từ DB (cần chỉnh lại DBManager để dùng row_factory)
            vehicle_type = slot[1]
            is_reserved = slot[2]
            status = slot[3] 
            
            col = i % cols
            row = i // cols
            x = col * (slot_width + spacing)
            y = row * (slot_height + spacing)
            
            max_height = max(max_height, y + slot_height + spacing)
            
            if status == 1:
                color = QColor("#EF4444") # Đỏ: Có xe
            elif is_reserved == 1:
                color = QColor("#FACC15") # Vàng: Trống, dành riêng cho khách tháng
            else:
                color = QColor("#10B981") # Xanh: Trống, vãng lai
                
            brush = QBrush(color)
            pen = QPen(QColor("#1F2937"), 2)
            
            self.parking_map_scene.addRect(x, y, slot_width, slot_height, pen, brush)
            text_id = self.parking_map_scene.addText(slot_id, font)
            text_id.setPos(x + 5, y + 5)
            
            status_text = "XE ĐANG ĐỖ" if status == 1 else vehicle_type
            text_type = self.parking_map_scene.addText(status_text, QFont("Arial", 9, QFont.Bold if status == 1 else QFont.Normal))
            text_type.setPos(x + 5, y + 25)
            text_type.setDefaultTextColor(QColor("#FFFFFF") if status == 1 else QColor("#1F2937"))

        parking_map_view = self.ui.findChild(QGraphicsView, "parkingMapView")
        if parking_map_view:
            self.parking_map_scene.setSceneRect(QRectF(0, 0, (slot_width + spacing) * cols, max_height))
            parking_map_view.fitInView(self.parking_map_scene.sceneRect(), Qt.KeepAspectRatio)


    # --- LOAD LAST ENTRY/EXIT INFO ON STARTUP ---

    def load_last_entry_exit_info(self):
        """Tải thông tin vào/ra cuối cùng từ DB và hiển thị trên giao diện khi khởi động"""
        try:
            # Tải thông tin vào cuối cùng
            last_entry = self.db.get_last_entry_session()
            if last_entry:
                session_id, plate_in, time_in, vehicle_type, slot_id = last_entry
                vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
                
                if self.lbl_entry_plate:
                    self.lbl_entry_plate.setText(f"{vehicle_icon} {plate_in} ({vehicle_type})")
                if self.lbl_entry_slot:
                    self.lbl_entry_slot.setText(f"Ô đỗ: {slot_id if slot_id else 'N/A'}")
                if self.lbl_entry_time:
                    # Format thời gian từ DB (YYYY-MM-DD HH:MM:SS) sang DD/MM/YYYY - HH:MM:SS
                    try:
                        time_obj = datetime.strptime(time_in, "%Y-%m-%d %H:%M:%S")
                        formatted_time = time_obj.strftime("%d/%m/%Y - %H:%M:%S")
                    except:
                        formatted_time = time_in
                    self.lbl_entry_time.setText(f"Thời gian: {formatted_time}")
                    
                print(f"[STARTUP] ✅ Loaded last entry: {plate_in} at {time_in} - Slot: {slot_id}")
            
            # Tải thông tin ra cuối cùng
            last_exit = self.db.get_last_exit_session()
            if last_exit:
                session_id, plate_in, time_out, price, payment_method, slot_id, vehicle_type = last_exit
                vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
                
                if self.lbl_exit_plate:
                    self.lbl_exit_plate.setText(f"{vehicle_icon} {plate_in} ({vehicle_type})")
                if self.lbl_exit_slot:
                    self.lbl_exit_slot.setText(f"Ô đỗ: {slot_id if slot_id else 'N/A'}")
                if self.lbl_exit_time_price:
                    # Format thời gian từ DB (YYYY-MM-DD HH:MM:SS) sang DD/MM/YYYY - HH:MM:SS
                    try:
                        time_obj = datetime.strptime(time_out, "%Y-%m-%d %H:%M:%S")
                        formatted_time = time_obj.strftime("%d/%m/%Y - %H:%M:%S")
                    except:
                        formatted_time = time_out
                    fee_text = f"{price:,}đ" if price else "0đ"
                    self.lbl_exit_time_price.setText(f"Thời gian: {formatted_time} | Phí: {fee_text}")
                    
                print(f"[STARTUP] ✅ Loaded last exit: {plate_in} ({vehicle_type}) at {time_out} - Slot: {slot_id}")
                
        except Exception as e:
            print(f"[STARTUP-ERROR] Lỗi load_last_entry_exit_info: {e}")

    # --- HELPER: DISPLAY ERROR ON ENTRY/EXIT LANE ---
    
    def display_entry_lane_error(self, error_msg, auto_clear_seconds=5):
        """Hiển thị lỗi trên cổng vào và tự động xóa sau timeout"""
        if self.lbl_entry_plate:
            self.lbl_entry_plate.setText(f"❌ {error_msg}")
            self.lbl_entry_plate.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        # Set timer để clear sau 5 giây
        def clear_entry():
            if self.lbl_entry_plate:
                self.lbl_entry_plate.setText("...")
                self.lbl_entry_plate.setStyleSheet("")
        
        QTimer.singleShot(auto_clear_seconds * 1000, clear_entry)
    
    def display_exit_lane_error(self, error_msg, auto_clear_seconds=5):
        """Hiển thị lỗi trên cổng ra và tự động xóa sau timeout"""
        if self.lbl_exit_plate:
            self.lbl_exit_plate.setText(f"❌ {error_msg}")
            self.lbl_exit_plate.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        # Set timer để clear sau 5 giây
        def clear_exit():
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText("...")
                self.lbl_exit_plate.setStyleSheet("")
        
        QTimer.singleShot(auto_clear_seconds * 1000, clear_exit)
    
    def clear_exit_lane_after_timeout(self, seconds=10):
        """Clear exit lane info sau khi xe ra được N giây"""
        def clear():
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText("...")
                self.lbl_exit_plate.setStyleSheet("")
            if self.lbl_exit_time_price:
                self.lbl_exit_time_price.setText("")
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("")
            if self.lbl_exit_slot:
                self.lbl_exit_slot.setText("")
        
        QTimer.singleShot(seconds * 1000, clear)

    # --- LOGIC XỬ LÝ CAMERA & LPR ---
    
    def update_entry_lpr(self, plate_text):
        print(f"[DEBUG] update_entry_lpr called with: {plate_text}")
        
        # Lọc ra biển số hợp lệ (không phải "...", "LỖI AI", etc.)
        if plate_text and plate_text != "..." and not plate_text.startswith("LỖI"):
            # Phân loại xe tự động
            vehicle_type = self.classify_vehicle_type(plate_text)
            vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
            
            if self.lbl_entry_plate:
                # Cập nhật thông tin biển số vào + loại xe
                self.lbl_entry_plate.setText(f"{vehicle_icon} {plate_text} ({vehicle_type})")
                print(f"[DEBUG] Entry plate updated: {plate_text} - Type: {vehicle_type}")
                
                # Cập nhật thời gian
                if self.lbl_entry_time:
                    from datetime import datetime
                    current_time = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
                    self.lbl_entry_time.setText(f"Thời gian: {current_time}")
            else:
                print("[DEBUG] lbl_entry_plate is None!")
                
            self.current_entry_plate = plate_text
            self.current_entry_vehicle_type = vehicle_type  # Lưu loại xe
            
            # Tự động trigger logic xử lý khi có biển số mới
            if self.lbl_entry_guidance:
                if self.txt_entry_rfid and self.txt_entry_rfid.text().strip():
                    self.lbl_entry_guidance.setText(
                        f"✅ Đã có RFID - Nhấn Enter để xác nhận"
                    )
                else:
                    self.lbl_entry_guidance.setText(
                        f"✅ {vehicle_icon} {vehicle_type} - Vui lòng quét thẻ RFID"
                    )
            
    def update_exit_lpr(self, plate_text):
        print(f"[DEBUG] update_exit_lpr called with: {plate_text}")

        if plate_text and plate_text != "..." and not plate_text.startswith("LỖI"):
            # Phân loại xe tự động
            vehicle_type = self.classify_vehicle_type(plate_text)
            vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
            
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText(f"{vehicle_icon} {plate_text} ({vehicle_type})")
                print(f"[DEBUG] Exit plate updated: {plate_text} - Type: {vehicle_type}")

            if self.lbl_exit_time_price:
                from datetime import datetime
                current_time = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
                self.lbl_exit_time_price.setText(f"Thời gian: {current_time}")

            self.current_exit_plate = plate_text

            # ✅ CHỈ hiển thị hướng dẫn
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("✅ Đã nhận diện biển số - Vui lòng xác nhận")

    def start_cameras(self):
        dashboard = self.loaded_pages.get("dashboard")
        if not dashboard:
            print("[DEBUG] Dashboard page not found!")
            return

        # Camera Cổng vào
        lbl_entry = dashboard.findChild(QLabel, "camEntryImage")
        print(f"[DEBUG] camEntryImage found: {lbl_entry is not None}")
        print(f"[DEBUG] CAMERA_ENTRY_ID: {CAMERA_ENTRY_ID}")
        
        if lbl_entry and CAMERA_ENTRY_ID is not None:
            # Bật camera cổng vào (chế độ snapshot - không xử lý AI liên tục)
            print(f"[DEBUG] Khởi tạo camera entry với ID: {CAMERA_ENTRY_ID}")
            self.camera_entry_thread = CameraThread(CAMERA_ENTRY_ID, enable_ai=ENABLE_AI_DETECTION)
            # Sử dụng partial hoặc closure riêng để tránh lambda capture sai biến
            def update_entry_frame(img):
                lbl_entry.setPixmap(QPixmap.fromImage(img))
            self.camera_entry_thread.change_pixmap_signal.connect(update_entry_frame)
            self.camera_entry_thread.capture_complete_signal.connect(self.on_entry_capture_complete)
            print("[DEBUG] ✅ Signal capture_complete_signal đã kết nối với on_entry_capture_complete")
            print("[DEBUG] Entry camera thread connected - CHẾ ĐỘ SNAPSHOT")
            self.camera_entry_thread.start()
            print("[DEBUG] Camera entry thread đã start")
        else:
            print("[DEBUG] Entry camera not started - label or camera ID missing")

        # Camera Cổng ra
        lbl_exit = dashboard.findChild(QLabel, "camExitImage")
        print(f"[DEBUG] camExitImage found: {lbl_exit is not None}")
        print(f"[DEBUG] CAMERA_EXIT_ID: {CAMERA_EXIT_ID}")
        
        if lbl_exit and CAMERA_EXIT_ID is not None and CAMERA_EXIT_ID != CAMERA_ENTRY_ID:
            # Bật camera cổng ra (chế độ snapshot - không xử lý AI liên tục)
            print(f"[DEBUG] Khởi tạo camera exit với ID: {CAMERA_EXIT_ID}")
            self.camera_exit_thread = CameraThread(CAMERA_EXIT_ID, enable_ai=ENABLE_AI_DETECTION)
            # Sử dụng closure riêng để tránh lambda capture sai biến
            def update_exit_frame(img):
                lbl_exit.setPixmap(QPixmap.fromImage(img))
            self.camera_exit_thread.change_pixmap_signal.connect(update_exit_frame)
            self.camera_exit_thread.capture_complete_signal.connect(self.on_exit_capture_complete)
            print("[DEBUG] Exit camera thread connected - CHẾ ĐỘ SNAPSHOT")
            self.camera_exit_thread.start()
            print("[DEBUG] Camera exit thread đã start")
        else:
            print(f"[DEBUG] Exit camera not started - label={lbl_exit is not None}, ID={CAMERA_EXIT_ID}, Same as entry={CAMERA_EXIT_ID == CAMERA_ENTRY_ID if CAMERA_EXIT_ID else 'N/A'}")
    
    # --- XỬ LÝ BARIE ---
    
    def handle_open_barrier_in(self):
        """Mở barie làn vào"""
        print("[INFO] 🚧 Mở barie làn vào")
        # Gửi lệnh mở barie xuống ESP32
        if self.network_server.is_connected():
            result = self.network_server.open_barrier(1)
            if result:
                print("[INFO] ✅ Lệnh mở barie làn 1 đã gửi thành công")
            else:
                print("[ERROR] ❌ Gửi lệnh mở barie làn 1 thất bại")
        else:
            print("[WARNING] ESP32 chưa kết nối. Không thể mở barie!")
    
    def handle_open_barrier_out(self):
        """Mở barie làn ra"""
        print("[INFO] 🚧 Mở barie làn ra")
        # Gửi lệnh mở barie xuống ESP32
        if self.network_server.is_connected():
            result = self.network_server.open_barrier(2)
            if result:
                print("[INFO] ✅ Lệnh mở barie làn 2 đã gửi thành công")
            else:
                print("[ERROR] ❌ Gửi lệnh mở barie làn 2 thất bại")
        else:
            print("[WARNING] ESP32 chưa kết nối. Không thể mở barie!")
    
    # --- XỬ LÝ SỰ KIỆN TỪ ESP32 ---
    
    def on_esp_card_scanned(self, card_uid, lane):
        """Xử lý khi ESP32 gửi thông tin quét thẻ hoặc checkout"""
        print(f"\n{'='*60}")
        print(f"[ESP-SCAN] 📡 Signal nhận từ ESP32")
        print(f"[ESP-SCAN] Lane: {lane}")
        print(f"[ESP-SCAN] Card UID: '{card_uid}' (empty={not card_uid})")
        print(f"{'='*60}\n")
        
        if lane == 1:
            # Làn vào - Phải có thẻ RFID
            print(f"[ESP-SCAN] 🚗 Xử lý làn VÀO (lane 1)")
            print(f"[ESP-SCAN] txt_entry_rfid exists: {self.txt_entry_rfid is not None if hasattr(self, 'txt_entry_rfid') else False}")
            
            if card_uid and self.txt_entry_rfid:
                print(f"[ESP-SCAN] ✅ Có thẻ RFID, điền vào field: {card_uid}")
                self.txt_entry_rfid.setText(card_uid)
                self.txt_entry_rfid.setFocus()
                print(f"[ESP-SCAN] Field value after setText: '{self.txt_entry_rfid.text()}'")
                
                # Gửi thông báo lên LCD ngay
                if hasattr(self, 'network_server'):
                    self.network_server.send_lcd_message("DANG XU LY...", f"The: {card_uid[:12]}")
                
                # Tự động trigger sau 500ms để user thấy được
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self.handle_rfid_scan)
                
                if self.lbl_entry_guidance:
                    self.lbl_entry_guidance.setText(f"📡 ESP: Nhận thẻ {card_uid}")
        
        elif lane == 2:
            # Làn ra - Có thể có hoặc không có thẻ
            print(f"[ESP-EXIT] 🚪 Xử lý làn RA (lane 2)")
            print(f"[ESP-EXIT] txt_exit_rfid exists: {self.txt_exit_rfid is not None if hasattr(self, 'txt_exit_rfid') else False}")
            
            if self.txt_exit_rfid:
                # DEBOUNCE: Kiểm tra thời gian quét gần nhất (time-based)
                current_time = time.time()
                if hasattr(self, '_last_exit_scan_time'):
                    time_diff = current_time - self._last_exit_scan_time
                    if time_diff < 5.0:  # 5 giây debounce
                        print(f"[ESP-EXIT] ⏱️ Debounce: {time_diff:.1f}s < 5s, bỏ qua")
                        return
                
                self._last_exit_scan_time = current_time
                print(f"[ESP-EXIT] ✅ Đã cập nhật _last_exit_scan_time")
                
                if card_uid:
                    # Có thẻ RFID (vé tháng hoặc vé lượt)
                    print(f"[ESP-EXIT] 🎫 Quét thẻ cổng ra: {card_uid}")
                    self.txt_exit_rfid.setText(card_uid)
                    print(f"[ESP-EXIT] Field value: '{self.txt_exit_rfid.text()}'")
                else:
                    # Không có thẻ (khách vãng lai checkout - message CHECKOUT:2)
                    print(f"[ESP-EXIT] 🚗 Checkout không thẻ (vãng lai) - trigger camera")
                    self.txt_exit_rfid.clear()
                
                self.txt_exit_rfid.setFocus()
                # Trigger xử lý ngay (có hoặc không có thẻ)
                print(f"[ESP-EXIT] 🔄 Sẽ gọi handle_exit_rfid_scan sau 500ms...")
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self.handle_exit_rfid_scan)
            else:
                print(f"[ESP-EXIT] ❌ txt_exit_rfid không tồn tại!")
    
    def on_esp_connected(self, ip):
        """Thông báo khi ESP32 kết nối"""
        print(f"[ESP] ✅ Kết nối thành công với ESP từ {ip}")
        # Hiển thị notification trên UI
        if hasattr(self, 'lbl_entry_guidance') and self.lbl_entry_guidance:
            self.lbl_entry_guidance.setText(f"✅ ESP32 connected ({ip})")
            self.lbl_entry_guidance.setStyleSheet("color: #22c55e; font-weight: bold;")
        
        # Gửi slot info ban đầu
        self.send_slot_info_to_esp()
        
        # Gửi LCD idle message ngay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self.send_idle_lcd_message)
    
    def on_esp_disconnected(self):
        """Thông báo khi ESP32 ngắt kết nối"""
        print(f"[ESP] ❌ ESP32 đã ngắt kết nối")
        if hasattr(self, 'lbl_entry_guidance') and self.lbl_entry_guidance:
            self.lbl_entry_guidance.setText("⚠️ ESP32 mất kết nối!")
    
    def on_barrier_closed(self, lane):
        """Xử lý khi barie đóng (xe đã qua)"""
        print(f"[BARRIER] 🚧 Barie làn {lane} đã đóng - Hiển thị số ô trống")
        # Gửi số ô trống lên LCD
        self.send_idle_lcd_message()
    
    def on_sensor_data_received(self, zone_id, status_binary, occupied, available):
        """
        Nhận dữ liệu từ Node cảm biến
        
        Args:
            zone_id: ID của zone (1-10)
            status_binary: Binary string 10 ký tự (VD: "1010001101")
            occupied: Số slot có xe
            available: Số slot trống
        """
        import time
        print(f"[SENSOR-HANDLER] Zone {zone_id}: {status_binary} | "
              f"Occupied={occupied}, Available={available}")
        
        # Cập nhật sensor manager
        self.sensor_manager.update_from_node(zone_id, status_binary, occupied, available)
        
        # CHỈ update UI nếu binary status THAY ĐỔI
        # VÀ cách lần update cuối cùng > 0.1 giây (debounce filter để tránh flicker)
        print(f"[SENSOR-CHECK] last={self._last_sensor_binary}, current={status_binary}, "
              f"time_diff={time.time() - self._last_sensor_binary_time:.2f}s")
        if self._last_sensor_binary != status_binary:
            current_time = time.time()
            time_since_last_update = current_time - self._last_sensor_binary_time
            
            if time_since_last_update >= 0.1:  # >= 0.1 giây từ lần update cuối (giảm từ 1.0s)
                print(f"[SENSOR-CHANGE-DETECTED] Binary changed: {self._last_sensor_binary} → {status_binary}")
                self._last_sensor_binary = status_binary
                self._last_sensor_binary_time = current_time
                
                # Cập nhật dashboard
                self.update_dashboard_with_sensor_data()
                
                # Cập nhật Parking Map realtime nếu tab đó đang hiển thị
                self.update_parking_map_realtime()
                
                # Gửi thông tin cập nhật lên LCD
                self.send_idle_lcd_message()
            else:
                # Bỏ qua - thay đổi quá nhanh (flicker)
                print(f"[SENSOR-FLICKER] Ignored rapid change: {status_binary} (only {time_since_last_update:.2f}s since last update)")
        else:
            # Binary không đổi - KHÔNG update UI (giảm spam)
            self._last_sensor_binary_time = time.time()  # Update timestamp dù không thay đổi binary
            pass
    
    def on_sensor_slots_changed(self, data):
        """
        Callback khi số chỗ trống thay đổi (từ sensor manager)
        
        Args:
            data: dict với motor_occupied, motor_available, car_occupied, car_available
        """
        print(f"[SENSOR-CHANGED] Motor: Occupied={data['motor_occupied']}, Available={data['motor_available']}, "
              f"Car: Occupied={data['car_occupied']}, Available={data['car_available']}")
        
        # KHÔNG gọi update_dashboard_with_sensor_data() ở đây để tránh trùng lặp
        # Vì on_sensor_data_received() đã gọi rồi
    
    def update_dashboard_with_sensor_data(self):
        """Cập nhật dashboard với dữ liệu từ cảm biến (bãi tổng hợp: 5 xe máy + 5 ô tô)"""
        try:
            print(f"\n[DASHBOARD-UPDATE-CALLED] ⚡ Dashboard update triggered!")
            # Lấy stats từ DB
            stats = self.db.get_parking_statistics()
            
            # Lấy số xe GUEST đang parking từ DB (chỉ GUEST, không MONTHLY)
            motor_db_guest_parking = stats['motor_guest_total'] - stats['motor_guest_available']
            car_db_guest_parking = stats['car_guest_total'] - stats['car_guest_available']
            
            print(f"[DASHBOARD-UPDATE-DB] Motor GUEST: Total={stats['motor_guest_total']}, "
                  f"Available={stats['motor_guest_available']}, Parking={motor_db_guest_parking}")
            print(f"[DASHBOARD-UPDATE-DB] Car GUEST: Total={stats['car_guest_total']}, "
                  f"Available={stats['car_guest_available']}, Parking={car_db_guest_parking}")
            
            # Lấy binary status từ sensor (10 bits)
            # Dùng current_binary_status property để auto-check timeout & reset nếu cần
            sensor_binary = self.sensor_manager.current_binary_status
            
            print(f"[DASHBOARD-UPDATE-SENSOR] Binary: {sensor_binary}")
            
            # Chia sensor thành 2 phần (PHẢI MATCH với sensor_manager.py):
            # - Slot 0-4 (5 bits đầu): XE MÁY (MOTOR)
            # - Slot 5-9 (5 bits cuối): Ô TÔ (CAR)
            motor_binary = sensor_binary[0:MOTOR_SLOTS]  # MOTOR_SLOTS bits đầu (0-4)
            car_binary = sensor_binary[MOTOR_SLOTS:MOTOR_SLOTS+CAR_SLOTS]   # CAR_SLOTS bits cuối (5-9)
            
            # Đếm số chỗ trống từ sensor (0 = trống, 1 = có xe)
            motor_sensor_available = motor_binary.count('0')  # Motor bits: 0-4
            car_sensor_available = car_binary.count('0')      # Car bits: 5-9
            
            # Tính số chỗ trống GUEST theo DB (không tính MONTHLY)
            motor_db_guest_available = stats['motor_guest_total'] - motor_db_guest_parking
            car_db_guest_available = stats['car_guest_total'] - car_db_guest_parking
            
            # ✅ LOGIC ĐÚNG: Lấy MIN (an toàn, không oversell)
            # - Nếu DB < Sensor: Lấy DB (DB ghi nhận có xe, sensor chưa thấy)
            # - Nếu Sensor < DB: Lấy Sensor (xe chiếm ô bãi)
            # Ví dụ: sensor=1, db=2 → min=1 (An toàn! 1 ô trống)
            motor_available_smart = min(motor_sensor_available, motor_db_guest_available)
            car_available_smart = min(car_sensor_available, car_db_guest_available)
            
            print(f"[DASHBOARD-UPDATE] Motor GUEST: sensor={motor_sensor_available}, db_guest={motor_db_guest_available}, result={motor_available_smart}")
            print(f"[DASHBOARD-UPDATE] Car GUEST: sensor={car_sensor_available}, db_guest={car_db_guest_available}, result={car_available_smart}")
            
            # ⚠️ Stat1 & Stat2 (số xe đang gửi) chỉ update từ DB khi có transaction
            # Không update ở đây để tránh fluctuation từ sensor
            # Chỉ update chỗ trống (dùng smart logic với sensor)
            # Cập nhật chỗ trống ô tô (dùng sensor + DB)
            if self.lbl_avail1_value:
                self.lbl_avail1_value.setText(f"{car_available_smart} / {stats['car_guest_total']} chỗ")
                
                # Thêm indicator nếu có dữ liệu cảm biến fresh
                if self.sensor_manager.is_data_fresh():
                    self.lbl_avail1_value.setStyleSheet("color: #22c55e; font-weight: bold;")
                else:
                    self.lbl_avail1_value.setStyleSheet("")
            else:
                print("[DASHBOARD-UPDATE-UI] ⚠️ lbl_avail1_value is None!")
            
            if self.lbl_avail1_progress:
                percentage = int((car_available_smart / stats['car_guest_total']) * 100) if stats['car_guest_total'] > 0 else 0
                self.lbl_avail1_progress.setValue(percentage)
                print(f"[DASHBOARD-UPDATE-UI] lbl_avail1_progress set to: {percentage}%")
            
            # Cập nhật chỗ trống xe máy (dùng sensor + DB, chỉ GUEST slots)
            if self.lbl_avail2_value:
                text = f"{motor_available_smart} / {stats['motor_guest_total']} chỗ"
                self.lbl_avail2_value.setText(text)
                print(f"[DASHBOARD-UPDATE-UI] lbl_avail2_value set to: {text}")
                
                # Thêm indicator nếu có dữ liệu cảm biến fresh
                if self.sensor_manager.is_data_fresh():
                    self.lbl_avail2_value.setStyleSheet("color: #22c55e; font-weight: bold;")
                else:
                    self.lbl_avail2_value.setStyleSheet("")
            else:
                print("[DASHBOARD-UPDATE-UI] ⚠️ lbl_avail2_value is None!")
            
            if self.lbl_avail2_progress:
                percentage = int((motor_available_smart / stats['motor_guest_total']) * 100) if stats['motor_guest_total'] > 0 else 0
                self.lbl_avail2_progress.setValue(percentage)
            
            # Cập nhật parking map (bất kể đang ở trang nào)
            if hasattr(self, 'parking_slots') and len(self.parking_slots) > 0:
                self.update_parking_map_realtime()
            
            print(f"[DASHBOARD-UPDATE] Motor GUEST: {motor_available_smart}/{stats['motor_guest_total']}, "
                  f"Car GUEST: {car_available_smart}/{stats['car_guest_total']}")
            
        except Exception as e:
            print(f"[DASHBOARD-ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    def send_idle_lcd_message(self):
        """Gửi LCD message idle state mỗi 10 giây (chỉ GUEST slots)"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            return
        
        try:
            # Lấy thống kê từ database
            stats = self.db.get_parking_statistics()
            if stats:
                # stats là dictionary, không phải tuple
                available_car = stats['car_guest_available']
                available_motor = stats['motor_guest_available']
                
                # Nếu có dữ liệu sensor fresh, dùng dữ liệu sensor thực tế
                if self.sensor_manager.is_data_fresh():
                    # Tính smart available từ sensor + DB (chỉ GUEST)
                    motor_db_guest_parking = stats['motor_guest_total'] - stats['motor_guest_available']
                    car_db_guest_parking = stats['car_guest_total'] - stats['car_guest_available']
                    smart_counts = self.sensor_manager.get_smart_available_count(
                        motor_db_guest_parking, car_db_guest_parking,
                        stats['motor_guest_total'], stats['car_guest_total']  # ✅ Thêm GUEST totals
                    )
                    available_car = smart_counts['car_available']
                    available_motor = smart_counts['motor_available']
                
                # Gửi lên LCD (chỉ GUEST slots)
                line1 = "SMART PARKING"
                line2 = f"OTO:{available_car} XM:{available_motor}"
                self.network_server.send_lcd_message(line1, line2)
                print(f"[ESP-LCD-IDLE] {line1} / {line2} (GUEST only)")
        except Exception as e:
            print(f"[ESP] Lỗi gửi idle LCD: {e}")
    
    def send_slot_info_to_esp(self):
        """Gửi thông tin số chỗ trống xuống ESP32 với dữ liệu từ cảm biến (chỉ GUEST slots)"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            return
        
        try:
            # Lấy thống kê từ database
            stats = self.db.get_parking_statistics()
            
            # Tính số chỗ trống thông minh cho từng loại (CHỈ GUEST)
            motor_db_guest_parking = stats['motor_guest_total'] - stats['motor_guest_available']
            car_db_guest_parking = stats['car_guest_total'] - stats['car_guest_available']
            
            smart_counts = self.sensor_manager.get_smart_available_count(motor_db_guest_parking, car_db_guest_parking)
            motor_available = smart_counts['motor_available']
            car_available = smart_counts['car_available']
            
            # Gửi xuống ESP: SLOTS:car:motor (chỉ GUEST slots)
            cmd = f"SLOTS:{car_available}:{motor_available}"
            self.network_server.send_command(cmd)
            print(f"[ESP] Gửi slot info (GUEST only): Car={car_available}/{stats['car_guest_total']}, Motor={motor_available}/{stats['motor_guest_total']}")
        except Exception as e:
            print(f"[ESP] Lỗi gửi slot info: {e}")
            
    # --- LOGIC XỬ LÝ GIAO DỊCH (ENTRY/EXIT) ---
    
    def on_rfid_text_changed(self, text):
        """Hiển thị hướng dẫn khi nhập RFID"""
        if text and self.lbl_entry_guidance:
            self.lbl_entry_guidance.setText(f"✏️ RFID: {text} - Nhấn Enter để chụp")
    
    def handle_rfid_scan(self):
        print(f"\n{'='*60}")
        print(f"[DEBUG] handle_rfid_scan() được gọi")
        rfid = self.txt_entry_rfid.text().strip()
        print(f"[DEBUG] RFID từ field: '{rfid}'")
        
        # DEBOUNCE: Kiểm tra xem thẻ này đã được xử lý chưa
        if hasattr(self, '_last_processed_card'):
            print(f"[DEBUG] Last processed card: '{self._last_processed_card}'")
            if self._last_processed_card == rfid and rfid:
                print(f"[DEBUG] ⚠️ Thẻ {rfid} đã được xử lý rồi, BỎ QUA!")
                print(f"{'='*60}\n")
                return
        else:
            print(f"[DEBUG] _last_processed_card chưa tồn tại, khởi tạo")
            self._last_processed_card = ""
        
        self.current_entry_card = rfid
        print(f"[DEBUG] ✅ Xử lý thẻ mới: '{rfid}'")
        
        if not rfid:
            print(f"[DEBUG] ⚠️ RFID trống, yêu cầu quét thẻ")
            self.lbl_entry_guidance.setText("⚠️ Vui lòng quét thẻ RFID.")
            print(f"{'='*60}\n")
            return
        
        # Trigger camera chụp ảnh và nhận diện
        print(f"[DEBUG] Kiểm tra camera thread...")
        print(f"[DEBUG] - hasattr(camera_entry_thread): {hasattr(self, 'camera_entry_thread')}")
        if hasattr(self, 'camera_entry_thread'):
            print(f"[DEBUG] - camera_entry_thread is not None: {self.camera_entry_thread is not None}")
            print(f"[DEBUG] - camera_entry_thread type: {type(self.camera_entry_thread)}")
        
        if self.lbl_entry_guidance:
            self.lbl_entry_guidance.setText("📸 Đang chụp ảnh và nhận diện...")
        
        if hasattr(self, 'camera_entry_thread') and self.camera_entry_thread:
            print("[DEBUG] ✅ Gọi camera_entry_thread.trigger_capture()")
            self.camera_entry_thread.trigger_capture()
            print(f"{'='*60}\n")
        else:
            print("[DEBUG] ❌ Camera không sẵn sàng!")
            if self.lbl_entry_guidance:
                self.lbl_entry_guidance.setText("❌ Camera không sẵn sàng!")
            print(f"{'='*60}\n")
            
    def on_entry_capture_complete(self, captured_image, plate_text):
        """Xử lý sau khi camera cổng vào chụp ảnh và nhận diện xong"""
        print(f"[DEBUG] ✅ on_entry_capture_complete() được gọi!")
        print(f"[ENTRY] Nhận được kết quả: {plate_text}")
        
        # Lưu ảnh vào file
        image_in_path = self.save_capture_image(captured_image, "entry")
        if image_in_path:
            print(f"[ENTRY-IMAGE] Lưu ảnh vào: {image_in_path}")
        
        # Hiển thị ảnh vừa chụp lên UI
        dashboard = self.loaded_pages.get("dashboard")
        if dashboard:
            lbl_entry = dashboard.findChild(QLabel, "camEntryImage")
            if lbl_entry:
                lbl_entry.setPixmap(QPixmap.fromImage(captured_image))
        
        # Cập nhật thông tin biển số
        self.update_entry_lpr(plate_text)
        
        # Phân loại xe
        vehicle_type = self.classify_vehicle_type(plate_text)
        print(f"[CLASSIFY] Biển số: {plate_text} → Loại xe: {vehicle_type}")
        
        # Xử lý logic vé tháng/vãng lai
        rfid = self.current_entry_card
        ticket_info = self.db.get_monthly_ticket_info(rfid)
        
        # Lưu image path để truyền vào record_entry()
        self._current_entry_image_path = image_in_path
        
        if ticket_info:
            plate_db = ticket_info['plate_number']
            slot_db = ticket_info['assigned_slot']
            vehicle_type_db = ticket_info['vehicle_type']
            
            # Kiểm tra biển số có khớp không
            if self.current_entry_plate != "..." and self.current_entry_plate != plate_db:
                error_msg = f"Biển số không khớp! Thẻ {rfid}: {plate_db} ≠ Camera: {self.current_entry_plate}"
                self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
                QMessageBox.warning(self, "Cảnh báo Vé tháng", 
                    f"Thẻ {rfid} của xe **{plate_db}** nhưng camera đọc: **{self.current_entry_plate}**! Kiểm tra lại.")
                self.lbl_entry_guidance.setText(f"⚠️ Biển số không khớp!")
                return
            
            # 🚗 Kiểm tra loại xe có khớp không (VÉ THÁNG CHỈ CHO LOẠI XE ĐÃ ĐĂNG KÝ)
            if vehicle_type != vehicle_type_db:
                error_msg = f"❌ Loại xe không khớp! Thẻ {rfid} đã đăng ký cho: {vehicle_type_db}\nNhưng camera nhận diện: {vehicle_type}"
                self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
                QMessageBox.warning(self, "Cảnh báo Loại xe", error_msg)
                self.lbl_entry_guidance.setText(f"⚠️ Loại xe không khớp!")
                return
            
            self.lbl_entry_guidance.setText(f"✅ KHÁCH THÁNG! Slot: {slot_db if slot_db else 'Vãng Lai'}")
            
            # TỰ ĐỘNG XỬ LÝ VÉ THÁNG - Không cần confirm thủ công
            if self.current_entry_plate != "...":
                self.auto_process_monthly_entry(rfid, plate_db, ticket_info)
            
        else:
            # TỰ ĐỘNG XỬ LÝ KHÁCH VÃNG LAI
            self.lbl_entry_guidance.setText("🚗 KHÁCH VÃNG LAI - Đang xử lý...")
            if self.current_entry_plate != "...":
                self.auto_process_guest_entry(rfid, self.current_entry_plate)
    
    def handle_exit_rfid_scan(self):
        """Xử lý khi quét thẻ RFID ở cổng ra (hoặc nhấn nút chụp)"""
        if not hasattr(self, 'txt_exit_rfid') or not self.txt_exit_rfid:
            return
        
        print(f"[EXIT-DEBUG] handle_exit_rfid_scan() được gọi")
        
        rfid = self.txt_exit_rfid.text().strip()
        
        if not rfid:
            # Nếu không có RFID, vẫn cho phép chụp (trường hợp khách vãng lai)
            print("[EXIT] Không có RFID - xe vãng lai checkout")
        
        # Trigger camera chụp ảnh
        if self.lbl_exit_fee:
            self.lbl_exit_fee.setText("📸 Đang chụp và nhận diện...")
        
        if hasattr(self, 'camera_exit_thread') and self.camera_exit_thread:
            # Kiểm tra camera có đang chạy không
            if not self.camera_exit_thread._run_flag:
                print("[EXIT] ⚠️ Camera đã dừng, khởi động lại...")
                try:
                    # Khởi động lại camera
                    self.camera_exit_thread._run_flag = True
                    if not self.camera_exit_thread.isRunning():
                        self.camera_exit_thread.start()
                    print("[EXIT] ✅ Camera đã được khởi động lại")
                except Exception as e:
                    print(f"[EXIT] ❌ Lỗi khởi động camera: {e}")
                    if self.lbl_exit_fee:
                        self.lbl_exit_fee.setText("❌ Lỗi camera!")
                    return
            
            self.camera_exit_thread.trigger_capture()
        else:
            print("[EXIT] ❌ Camera thread không tồn tại!")
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("❌ Camera không sẵn sàng!")
    
    def on_exit_capture_complete(self, captured_image, plate_text):
        """Xử lý sau khi camera cổng ra chụp ảnh và nhận diện xong"""
        print(f"[EXIT] Nhận được kết quả: {plate_text}")
        
        # Lưu ảnh vào file
        image_out_path = self.save_capture_image(captured_image, "exit")
        if image_out_path:
            print(f"[EXIT-IMAGE] Lưu ảnh vào: {image_out_path}")
        
        # Hiển thị ảnh vừa chụp lên UI
        dashboard = self.loaded_pages.get("dashboard")
        if dashboard:
            lbl_exit = dashboard.findChild(QLabel, "camExitImage")
            if lbl_exit:
                lbl_exit.setPixmap(QPixmap.fromImage(captured_image))
        
        # Lưu image path để truyền vào record_exit()
        self._current_exit_image_path = image_out_path
        
        # Cập nhật thông tin biển số và tính phí
        self.update_exit_lpr(plate_text)
        
        # Gửi thông tin xe lên LCD ESP32 khi nhận diện được biển số
        if plate_text and plate_text != "..." and not plate_text.startswith("LỖI"):
            vehicle_type = self.classify_vehicle_type(plate_text)
            # Gửi biển số vào LCD để xác nhận
            self.send_vehicle_info_to_lcd(plate_text, vehicle_type, "Ra bãi")
            print(f"[ESP-LCD] ✅ Đã gửi thông tin xe ra lên LCD: {plate_text} ({vehicle_type})")
    
    def auto_process_monthly_entry(self, card_id, plate, ticket_info):
        """Tự động xử lý xe vé tháng vào bãi"""
        vehicle_type = ticket_info['vehicle_type']
        assigned_slot = ticket_info['assigned_slot']
        
        # Kiểm tra slot có bị chiếm không
        slot_status = self.db.get_all_parking_slots()
        is_reserved_slot_occupied = any(s[0] == assigned_slot and s[3] == 1 for s in slot_status if assigned_slot)
        
        if assigned_slot and not is_reserved_slot_occupied:
            # Slot riêng còn trống
            pass
        else:
            # Slot riêng bị chiếm hoặc không có, tìm slot khác
            assigned_slot = self.db.find_available_slot(vehicle_type, is_monthly=False)
            if not assigned_slot:
                error_msg = "Bãi đỗ xe đã đầy!"
                self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
                QMessageBox.warning(self, "Lỗi", error_msg)
                return
        
        # Ghi nhận xe vào
        image_path = getattr(self, '_current_entry_image_path', None)
        success = self.db.record_entry(card_id, plate, vehicle_type, assigned_slot, 'MONTHLY', image_path)
        
        if success:
            # Set debounce flag để tránh xử lý lại cùng thẻ
            self._last_processed_card = card_id
            
            # Gửi thông tin lên LCD ESP32
            owner_name = ticket_info.get('owner_name', '')
            self.send_vehicle_info_to_lcd(plate, vehicle_type, assigned_slot, owner_name)
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            
            # Hiển thị thông báo ngắn
            self.lbl_entry_guidance.setText(f"✅ Vào tại: {assigned_slot} - 🚧 Barie đã mở")
            print(f"[AUTO] Khách tháng {plate} vào slot {assigned_slot}")
            
            # Cập nhật slot trên dashboard (có loại vé)
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(f"Ô đỗ: {assigned_slot} (VÉ THÁNG)")
                print(f"[DASHBOARD] ✅ Entry slot updated: {assigned_slot}")
            else:
                print(f"[DASHBOARD] ⚠️ lbl_entry_slot is None!")
            
            # Cập nhật slot info
            self.send_slot_info_to_esp()
            
            # Gửi số ô trống lên LCD sau khi xe vé tháng vào (delay 3s để người dùng thấy thông tin xe)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.send_idle_lcd_message)
            
            # Cập nhật UI
            self.draw_parking_map()
            self.update_dashboard_stats()

            #Cập nhật lịch sử ra vào
            self.refresh_history_if_visible()

        else:
            error_msg = "Không thể ghi nhận xe vào."
            self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi", error_msg)
    
    def auto_process_guest_entry(self, card_id, plate):
        """Tự động xử lý khách vãng lai vào bãi"""
        # Phân loại xe tự động
        vehicle_type = self.classify_vehicle_type(plate)
        print(f"[CLASSIFY] Biển số: {plate} → Loại xe: {vehicle_type}")
        ticket_type = 'GUEST'
        
        print(f"[ENTRY] Tìm slot cho {vehicle_type}...")
        
        # Tìm slot trống
        assigned_slot = self.db.find_available_slot(vehicle_type, is_monthly=False)
        
        if not assigned_slot:
            # Kiểm tra thông tin chi tiết - dùng guest-available slots (bỏ qua reserved)
            # Ưu tiên dùng sensor data nếu có sẵn (accurate real-time data)
            available, total = self.db.get_available_slots_for_guests(vehicle_type)
            
            # Nếu sensor có data fresh, dùng sensor available count thay vì DB
            if self.sensor_manager.is_data_fresh():
                stats = self.db.get_parking_statistics()
                if vehicle_type == 'Ô tó':
                    available = stats['car_guest_available']
                    total = stats['car_guest_total']
                    print(f"[ENTRY-SENSOR] Using sensor data: Car GUEST available={available}/{total}")
                elif vehicle_type == 'Xe máy':
                    available = stats['motor_guest_available']
                    total = stats['motor_guest_total']
                    print(f"[ENTRY-SENSOR] Using sensor data: Motor GUEST available={available}/{total}")
            
            error_msg = f"❌ Bãi đầy! {vehicle_type}: {available}/{total} chỗ trống"
            print(f"[ENTRY ERROR] {error_msg}")
            self.lbl_entry_guidance.setText(error_msg)
            
            # Gửi thông báo lên LCD ESP32
            if self.network_server.is_connected():
                self.network_server.send_lcd_message("BAI DAY!", f"{vehicle_type}: {available}/{total}")
                print(f"[ESP-LCD] Đã gửi thông báo bãi đầy lên LCD")
            else:
                print(f"[ESP-LCD] ⚠️ ESP32 chưa kết nối, không thể gửi LCD")
            
            # Reset UI về trạng thái ban đầu sau 10 giây
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10000, self.reset_entry_ui)
            return
        
        # Ghi nhận xe vào
        image_path = getattr(self, '_current_entry_image_path', None)
        success = self.db.record_entry(card_id, plate, vehicle_type, assigned_slot, ticket_type, image_path)
        
        if success:
            # Set debounce flag để tránh xử lý lại cùng thẻ
            self._last_processed_card = card_id
            
            # Gửi thông tin lên LCD ESP32
            self.send_vehicle_info_to_lcd(plate, vehicle_type, assigned_slot)
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            # Cập nhật lịch sử ra vào 
            self.refresh_history_if_visible()

            
            # Hiển thị thông báo ngắn
            self.lbl_entry_guidance.setText(f"✅ Vãng lai vào tại: {assigned_slot} - 🚧 Barie đã mở")
            print(f"[AUTO] Khách vãng lai {plate} vào slot {assigned_slot}")
            
            # Cập nhật slot trên dashboard (có loại vé)
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(f"Ô đỗ: {assigned_slot} (KHÁCH VÃNG LAI)")
                print(f"[DASHBOARD] ✅ Entry slot updated: {assigned_slot}")
            else:
                print(f"[DASHBOARD] ⚠️ lbl_entry_slot is None!")

            
            # Cập nhật UI
            self.draw_parking_map()
            self.update_dashboard_stats()
            
            # Gửi số ô trống lên LCD sau 3 giây (để người dùng thấy thông tin xe)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.send_idle_lcd_message)
        else:
            self.lbl_entry_guidance.setText("❌ Lỗi ghi dữ liệu!")
    
    def send_vehicle_info_to_lcd(self, plate, vehicle_type, slot, owner_name=""):
        """Gửi thông tin xe lên LCD ESP32"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            print("[ESP-LCD] ⚠️ ESP32 chưa kết nối - Không thể hiển thị LCD")
            return
        
        try:
            # Hiển thị: Dòng 1 = Biển số, Dòng 2 = Loại xe + Slot
            line1 = plate[:16]  # Giới hạn 16 ký tự
            line2 = f"{vehicle_type} | {slot}"[:16]
            
            # Nếu có tên chủ (vé tháng), hiển thị ở dòng 2
            if owner_name:
                line2 = owner_name[:16]
            
            self.network_server.send_lcd_message(line1, line2)
            print(f"[ESP-LCD] {line1} / {line2}")
            
            # ⚠️ LƯU Ý: Caller có trách nhiệm schedule send_idle_lcd_message() nếu cần
            # (Tránh conflict với multiple timers gọi cùng lúc)
            
        except Exception as e:
            print(f"[ESP] Lỗi gửi LCD: {e}")
    

    
    def send_fee_to_lcd(self, fee):
        """Gửi phí thanh toán lên LCD ESP32"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            print("[ESP-LCD] ⚠️ ESP32 chưa kết nối - Không thể hiển thị phí")
            return
        
        try:
            # Hiển thị: Dòng 1 = "THANH TOAN", Dòng 2 = Số tiền
            line1 = "THANH TOAN"
            line2 = f"Phi: {fee:,}d"[:16]
            
            self.network_server.send_lcd_message(line1, line2)
            print(f"[ESP-LCD] {line1} / {line2}")
        except Exception as e:
            print(f"[ESP] Lỗi gửi LCD: {e}")
    
    def reset_entry_ui(self):
        """Reset giao diện cổng vào về trạng thái ban đầu"""
        print("[RESET] Đang reset UI cổng vào...")
        
        # Reset biến trạng thái
        self.current_entry_plate = "..."
        self.current_entry_card = ""
        self._last_processed_card = ""  # Reset debounce
        
        # Reset UI elements
        if self.lbl_entry_plate:
            self.lbl_entry_plate.setText("...")
        if self.txt_entry_rfid:
            self.txt_entry_rfid.clear()
        
        
        # Gửi idle message lên LCD
        if hasattr(self, 'network_server') and self.network_server.is_connected():
            self.send_idle_lcd_message()
        
        # Cập nhật lại slot info
        self.send_slot_info_to_esp()
        
        print("[RESET] ✅ Đã reset xong")

    def classify_vehicle_type(self, plate_text):
        """
        Phân loại xe dựa trên định dạng biển số từ OCR.
        
        Logic phân loại:
        - Xe máy: Có dấu ngăn cách (space hoặc hyphen) giữa mã tỉnh và chữ cái
          VD: "12-B1", "35-B2 633.71", "51H 919.91"
        - Ô tô: Không có dấu ngăn cách (số và chữ dính liền)
          VD: "51F", "29A12345"
        
        Args:
            plate_text (str): Text biển số đã nhận dạng từ OCR
            
        Returns:
            str: "Xe máy" hoặc "Ô tô"
        """
        import re
        
        if not plate_text:
            return "Ô tô"  # Default
        
        # Normalize: uppercase, loại bỏ dấu chấm và khoảng trắng thừa
        plate = plate_text.upper().strip()
        # Loại bỏ dấu chấm (.) nhưng giữ lại dấu gạch ngang (-) và space
        plate = plate.replace('.', '')
        print(f"[CLASSIFY-DEBUG] Original: '{plate_text}' | Normalized: '{plate}'")
        
        # Kiểm tra pattern xe máy: Có dấu ngăn cách sau mã tỉnh (2 số)
        # Pattern 1: XX-Y... (có dấu gạch ngang)
        # Pattern 2: XX Y... (có khoảng trắng)
        if re.match(r'^\d{2}[\s\-][A-Z]', plate):
            print(f"[CLASSIFY-DEBUG] Result: Xe máy (có dấu ngăn cách)")
            return "Xe máy"
        
        # Kiểm tra pattern ô tô: Số và chữ dính liền (không có dấu ngăn cách)
        # Pattern: XXY... (51F, 29A, etc.)
        if re.match(r'^\d{2}[A-Z]', plate):
            print(f"[CLASSIFY-DEBUG] Result: Ô tô (không có dấu ngăn cách)")
            return "Ô tô"
        
        # Fallback: Nếu không match pattern nào, dùng logic độ dài
        # Xe máy thường ngắn hơn ô tô
        clean_plate = re.sub(r'[^A-Z0-9]', '', plate)
        if len(clean_plate) <= 7:
            print(f"[CLASSIFY-DEBUG] Result: Xe máy (fallback: length {len(clean_plate)} <= 7)")
            return "Xe máy"
        else:
            print(f"[CLASSIFY-DEBUG] Result: Ô tô (fallback: length {len(clean_plate)} > 7)")
            return "Ô tô"
    
    def handle_confirm_entry(self):
        plate = self.current_entry_plate
        card_id = self.txt_entry_rfid.text().strip()
        
        if plate == "..." or not card_id:
            error_msg = "Đợi biển số & nhập Mã RFID"
            self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng đợi nhận diện biển số và nhập Mã RFID.")
            return
            
        ticket_info = self.db.get_monthly_ticket_info(card_id)
        
        if ticket_info:
            ticket_type = 'MONTHLY'
            vehicle_type = ticket_info['vehicle_type']
            assigned_slot = ticket_info['assigned_slot'] 
            
            slot_status = self.db.get_all_parking_slots() # Cần lấy thông tin chi tiết
            is_reserved_slot_occupied = any(s[0] == assigned_slot and s[3] == 1 for s in slot_status if assigned_slot)
            
            if assigned_slot and not is_reserved_slot_occupied:
                pass 
            else:
                assigned_slot = self.db.find_available_slot(vehicle_type, is_monthly=False) 
        else:
            ticket_type = 'GUEST'
            # Sử dụng vehicle_type đã phân loại từ camera
            vehicle_type = self.current_entry_vehicle_type
            print(f"[DEBUG] Using classified vehicle type: {vehicle_type} for plate: {plate}")
            assigned_slot = self.db.find_available_slot(vehicle_type, is_monthly=False)

        if not assigned_slot:
            error_msg = f"Bãi đỗ xe đã đầy cho loại xe {vehicle_type}! Không thể cho xe vào."
            self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi", error_msg)
            return

        success = self.db.record_entry(card_id, plate, vehicle_type, assigned_slot, ticket_type)
        
        if success:
            # Gửi thông tin lên LCD ESP32
            self.send_vehicle_info_to_lcd(plate, vehicle_type, assigned_slot)
            
            # 📺 Sau 3 giây, LCD tự động quay lại hiển thị số ô trống
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.send_idle_lcd_message)
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            
            # 📋 Cập nhật thông tin chi tiết xe đã vào trên UI
            vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
            if self.lbl_entry_plate:
                self.lbl_entry_plate.setText(f"{vehicle_icon} {plate} ({vehicle_type})")
                self.lbl_entry_plate.setStyleSheet("color: #22c55e; font-weight: bold;")
            
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(f"Ô đỗ: {assigned_slot}")
            
            if self.lbl_entry_guidance:
                ticket_type_text = "VÉ THÁNG" if ticket_type == "MONTHLY" else "VÉ LƯỢT"
                self.lbl_entry_guidance.setText(f"✅ {ticket_type_text} - Vào tại: {assigned_slot} - 🚧 Barie đã mở")
            
            QMessageBox.information(self, "Xe Vào Thành Công", f"Xe {plate} ({ticket_type}) đã đỗ tại {assigned_slot}.\n🚧 Barie đã mở!")
            self.txt_entry_rfid.clear()
            self.current_entry_plate = "..."
            self.draw_parking_map()
            self.update_dashboard_stats()  # Cập nhật thống kê 
        else:
            error_msg = "Không thể ghi nhận xe vào."
            self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi Database", error_msg)
            
    def calculate_fee_and_display(self, exit_plate):
        session = self.db.get_parking_session(plate=exit_plate, status='PARKING')
        if not session:
            self.lbl_exit_fee.setText("Xe không có trong bãi")
            return 0, None, None, None

        time_in_str = session[4] # time_in ở index 4
        vehicle_type = session[9] # vehicle_type ở index 9
        ticket_type = session[10] # ticket_type ở index 10
        slot_id = session[13] if len(session) > 13 else None # slot_id ở index 13 (mới thêm)
        
        # Hiển thị thông tin chỗ đỗ (có loại vé)
        if slot_id and self.lbl_exit_slot:
            ticket_type_text = "VÉ THÁNG" if ticket_type == 'MONTHLY' else "KHÁCH VÃNG LAI"
            self.lbl_exit_slot.setText(f"Ô đỗ: {slot_id} ({ticket_type_text})")
            print(f"[DASHBOARD] ✅ Exit slot updated: {slot_id} ({ticket_type_text})")
        elif self.lbl_exit_slot:
            print(f"[DASHBOARD] ⚠️ slot_id is None!")
        
        # Kiểm tra vé tháng - MIỄN PHÍ
        if ticket_type == 'MONTHLY':
            self.lbl_exit_fee.setText("✅ VÉ THÁNG - MIỄN PHÍ")
            # Gửi info lên LCD
            self.send_vehicle_info_to_lcd(exit_plate, vehicle_type, slot_id, "VE THANG")
            # Tự động xử lý xe ra cho vé tháng
            self.auto_process_monthly_exit(exit_plate, session[0])
            return 0, session[0], slot_id, 'MONTHLY'
        
        # Tính phí và thời gian đỗ
        current_time_seconds = time.time()
        fee = calculate_parking_fee(self.db, vehicle_type, time_in_str, current_time_seconds)
        
        # Tính thời gian đỗ (phải dùng cách tính giống hệt như calculate_parking_fee)
        time_in = time.mktime(time.strptime(time_in_str, "%Y-%m-%d %H:%M:%S"))
        parking_duration_minutes = (current_time_seconds - time_in) / 60
        
        # Chuyển đổi phút thành giờ:phút
        hours = int(parking_duration_minutes // 60)
        minutes = int(parking_duration_minutes % 60)
        duration_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        self.lbl_exit_fee.setText(f"{fee:,} VND ({duration_text})")
        print(f"[FEE] Exit plate: {exit_plate}, Duration: {hours}h {minutes}m ({int(parking_duration_minutes)} mins total), Fee: {fee}")
        
        # Gửi thông tin xe và phí lên LCD
        self.send_vehicle_info_to_lcd(exit_plate, vehicle_type, slot_id)
        
        # Gửi phí sau 1.5 giây để người dùng thấy thông tin xe trước
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda fee=fee: self.send_fee_to_lcd(fee))
        
        # Gửi số ô trống lên LCD sau 3 giây
        QTimer.singleShot(3000, self.send_idle_lcd_message)
        
        return fee, session[0], slot_id, ticket_type # fee, id, slot_id, ticket_type
    
    def auto_process_monthly_exit(self, plate, session_id):
        image_path = getattr(self, '_current_exit_image_path', None)
        success = self.db.record_exit(session_id, plate, 0, 'MONTHLY', image_path)

        if success:
            self.handle_open_barrier_out()
        # ✅ RESET debounce cho thẻ
            self._last_processed_card = ""

            # 📺 Không auto-reset - giữ thông tin để xem được
            self.draw_parking_map()
            self.update_dashboard_stats()
            self.refresh_history_if_visible()
            
            # Gửi số ô trống lên LCD sau khi xe vé tháng ra (delay 3s để người dùng thấy thông tin xe)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.send_idle_lcd_message)


        else:
            error_msg = "Không thể ghi nhận xe ra."
            self.display_exit_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi", error_msg)
    
    def reset_exit_ui(self):
        """Reset giao diện cổng ra"""
        self.current_exit_plate = "..."
        if self.lbl_exit_plate:
            self.lbl_exit_plate.setText("...")
        if self.lbl_exit_fee:
            self.lbl_exit_fee.setText("0 VND")
        
    def handle_confirm_exit(self):
        exit_plate = self.current_exit_plate
        
        if exit_plate == "...":
            error_msg = "Vui lòng đợi nhận diện biển số xe ra."
            self.display_exit_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.warning(self, "Thiếu thông tin", error_msg)
            return
            
        fee, session_id, slot_id, ticket_type = self.calculate_fee_and_display(exit_plate)

        if session_id is None:
            error_msg = f"Không tìm thấy xe {exit_plate} đang đỗ."
            self.display_exit_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.warning(self, "Lỗi", error_msg)
            return
        
        # Vé tháng đã được xử lý tự động trong calculate_fee_and_display
        if ticket_type == 'MONTHLY':
            return
        
        # Lấy loại xe từ session
        session = self.db.get_parking_session(plate=exit_plate, status='PARKING')
        vehicle_type = session[9] if session else "Ô tô"  # index 9 là vehicle_type

        # Hiển thị dialog thanh toán cho khách vãng lai
        payment_dialog = PaymentDialog(exit_plate, vehicle_type, fee, self)
        if payment_dialog.exec() != QDialog.Accepted or not payment_dialog.payment_confirmed:
            QMessageBox.information(self, "Hủy", "Thanh toán đã bị hủy. Xe chưa được phép ra.")
            return
        
        # Thanh toán thành công -> Ghi nhận xe ra
        payment_method = payment_dialog.payment_method
        image_path = getattr(self, '_current_exit_image_path', None)
        success = self.db.record_exit(session_id, exit_plate, fee, payment_method, image_path)
        
        if success:
            # Tự động mở barie
            self.handle_open_barrier_out()
            # ✅ RESET debounce để thẻ dùng lại được
            self._last_processed_card = ""

            self.refresh_history_if_visible()
            
            # � Gửi thông tin thanh toán lên LCD
            self.send_fee_to_lcd(fee)
            
            # 📺 Sau 2 giây, LCD tự động quay lại hiển thị số ô trống
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, self.send_idle_lcd_message)
            
            # �📋 Cập nhật thông tin chi tiết xe đã ra trên UI
            vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText(f"{vehicle_icon} {exit_plate} ({vehicle_type})")
                self.lbl_exit_plate.setStyleSheet("color: #22c55e; font-weight: bold;")
            
            if self.lbl_exit_time_price:
                self.lbl_exit_time_price.setText(f"Thời gian: {time.strftime('%d/%m/%Y - %H:%M:%S', time.localtime())} | Phí: {fee:,} VND")
            
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText(f"Thanh toán: {fee:,} VND ({payment_method})")
            
            QMessageBox.information(self, "Xe Ra Thành Công", 
                f"✅ Đã thanh toán {fee:,} VND\n"
                f"Phương thức: {payment_method}\n"
                f"🚧 Barie đã mở!")
            
            # Clear exit lane info after 10 seconds (successful exit)
            # 📺 Khôngauto-reset - giữ thông tin để xem được
            
            self.current_exit_plate = "..."
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText("...")
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("0 VND")
            
            # Reset exit processing flag
            self._exit_processing = False
            
            # ✅ RESET RFID field và debounce để cho phép quét tiếp
            if self.txt_exit_rfid:
                self.txt_exit_rfid.clear()
                self.txt_exit_rfid.setFocus()
            self._last_exit_scan_time = 0  # Reset debounce time
            
            # Reset entry UI để thẻ này có thể dùng lại cho xe khác
            self.reset_entry_ui()
            
            self.draw_parking_map()
            self.update_dashboard_stats()  # Cập nhật thống kê
        else:
            error_msg = "Lỗi ghi nhận xe ra vào Database."
            self.display_exit_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi", error_msg)
            self._exit_processing = False
            
            # ✅ RESET RFID field để cho phép quét lại
            if self.txt_exit_rfid:
                self.txt_exit_rfid.clear()
            self._last_exit_scan_time = 0  # Reset debounce time
            
    # --- LOGIC TRANG VÉ THÁNG (MONTHLY) ---
    
    def setup_monthly_page(self, widget):
        """Thiết lập các kết nối cho trang vé tháng"""
        btn_register = widget.findChild(QPushButton, "btnRegisterSubmit")
        if btn_register:
            btn_register.clicked.connect(self.handle_register_monthly)
        else:
            print("[WARNING] btnRegisterSubmit not found in monthly page")
        
        btn_upload = widget.findChild(QPushButton, "btnUploadAvatar")
        if btn_upload:
            btn_upload.clicked.connect(self.handle_upload_avatar)
        
        btn_scan_card = widget.findChild(QPushButton, "btnScanCard")
        if btn_scan_card:
            btn_scan_card.clicked.connect(self.handle_scan_card_monthly)
        else:
            print("[WARNING] btnScanCard not found in monthly page")
        
        # Kết nối ô tìm kiếm
        search_input = widget.findChild(QLineEdit, "monthlySearch")
        if search_input:
            search_input.textChanged.connect(self.handle_monthly_search)
        
        # Tìm hoặc tạo label để hiển thị thống kê vé tháng
        self.monthly_stats_label = widget.findChild(QLabel, "monthlyStatsLabel")
        if not self.monthly_stats_label:
            # Nếu không tìm thấy, tạo mới và thêm vào layout
            from PySide6.QtWidgets import QVBoxLayout
            self.monthly_stats_label = QLabel()
            self.monthly_stats_label.setObjectName("monthlyStatsLabel")
            self.monthly_stats_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1f2937;")
            # Thêm vào layout đầu tiên của widget nếu có
            main_layout = widget.layout()
            if main_layout and main_layout.count() > 0:
                main_layout.insertWidget(0, self.monthly_stats_label)
        
        # Khởi tạo biến lưu đường dẫn ảnh
        self.selected_avatar_path = ""
        
        # Load dữ liệu vé tháng ban đầu
        self.load_monthly_tickets()
    
    def load_monthly_tickets(self, search_query=""):
        page = self.loaded_pages.get("monthly")
        if not page: return
        table = page.findChild(QTableWidget, "monthlyTable")
        if not table: return
        
        try:
            # Tải và hiển thị thống kê vé tháng
            stats = self.db.get_monthly_ticket_stats()
            if hasattr(self, 'monthly_stats_label') and self.monthly_stats_label:
                stats_text = (f"📊 Xe máy: {stats['motor_registered']}/{stats['motor_total']} | "
                             f"Ô tô: {stats['car_registered']}/{stats['car_total']}")
                self.monthly_stats_label.setText(stats_text)
                print(f"[MONTHLY-PAGE] {stats_text}")
            
            # Hiển thị header
            table.horizontalHeader().setVisible(True)
            table.verticalHeader().setVisible(True)
            
            from datetime import datetime
            tickets = self.db.get_all_monthly_tickets(search_query)
            headers = ["Biển số", "Chủ xe", "Mã thẻ", "Loại xe", "Đăng ký", "Hết hạn", "Ô đỗ riêng", "Ảnh đại diện", "Trạng thái", "Thao tác"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(tickets))
            
            for row_idx, row_data in enumerate(tickets):
                # Hiển thị các cột dữ liệu (7 cột đầu từ DB)
                for col_idx in range(7):
                    val = row_data[col_idx] if col_idx < len(row_data) else ""
                    item = QTableWidgetItem(str(val) if val else "")
                    table.setItem(row_idx, col_idx, item)
                
                # Cột 8: Nút xem ảnh đại diện
                btn_view_avatar = QPushButton("Xem ảnh")
                btn_view_avatar.setProperty("card_id", row_data[2] if len(row_data) > 2 else "")  # Lưu mã thẻ
                btn_view_avatar.clicked.connect(lambda checked, card=row_data[2]: self.view_member_avatar(card))
                table.setCellWidget(row_idx, 7, btn_view_avatar)
                
                # Cột 9: Trạng thái
                status_db = row_data[8] if len(row_data) > 8 else "ACTIVE"
                exp_date_str = row_data[9] if len(row_data) > 9 else ""
                
                # Tính trạng thái hiển tại
                if status_db == "DELETED":
                    status_text = "Đã xóa"
                    status_color = "#EF4444"  # Đỏ
                elif exp_date_str:
                    try:
                        exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                        if exp_date < datetime.now():
                            status_text = "Hết hạn"
                            status_color = "#F59E0B"  # Vàng
                        else:
                            status_text = "Đang hoạt động"
                            status_color = "#10B981"  # Xanh
                    except:
                        status_text = "Đang hoạt động"
                        status_color = "#10B981"
                else:
                    status_text = "Đang hoạt động"
                    status_color = "#10B981"
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor(status_color))
                table.setItem(row_idx, 8, status_item)
                
                # Cột 10: Nút Gia hạn và Xóa
                if status_db != "DELETED":
                    # Tạo widget chứa 2 nút
                    action_widget = QWidget()
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 2, 2, 2)
                    action_layout.setSpacing(5)
                    
                    # Nút Gia hạn
                    btn_extend = QPushButton("Gia hạn")
                    btn_extend.setStyleSheet("background-color: #3B82F6; color: white; padding: 5px;")
                    btn_extend.clicked.connect(lambda checked, card=row_data[2], exp=row_data[5]: self.extend_monthly_ticket_dialog(card, exp))
                    action_layout.addWidget(btn_extend)
                    
                    # Nút Xóa
                    btn_delete = QPushButton("Xóa")
                    btn_delete.setStyleSheet("background-color: #EF4444; color: white; padding: 5px;")
                    btn_delete.clicked.connect(lambda checked, card=row_data[2]: self.delete_monthly_ticket(card))
                    action_layout.addWidget(btn_delete)
                    
                    table.setCellWidget(row_idx, 9, action_widget)
                else:
                    # Nếu đã xóa thì hiển thị text
                    deleted_item = QTableWidgetItem("---")
                    deleted_item.setForeground(QColor("#999"))
                    table.setItem(row_idx, 9, deleted_item)
            
            # ✅ Auto-resize cột để vừa nội dung
            table.resizeColumnsToContents()
            print(f"[MONTHLY-LOAD] ✅ Loaded {len(tickets)} tickets successfully")
            
        except Exception as e:
            print(f"[MONTHLY-LOAD-ERROR] {e}")
            import traceback
            traceback.print_exc()

    def handle_register_monthly(self):
        page = self.loaded_pages.get("monthly")
        plate = page.findChild(QLineEdit, "newPlate").text().strip()
        owner = page.findChild(QLineEdit, "newOwner").text().strip()
        card = page.findChild(QLineEdit, "newCardNumber").text().strip()
        v_type_cb = page.findChild(QComboBox, "newType")
        v_type = v_type_cb.currentText() if v_type_cb else "Ô tô"
        reg_date = page.findChild(QDateEdit, "newRegDate").date().toString("yyyy-MM-dd")
        exp_date = page.findChild(QDateEdit, "newExpDate").date().toString("yyyy-MM-dd")
        
        # Validate
        if not plate or not owner or not card:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng điền đầy đủ thông tin!")
            return
        
        # Tính phí vé tháng
        monthly_fee = 500000 if v_type == "Ô tô" else 200000  # Giá cố định
        
        # Hiển thị dialog thanh toán
        print(f"[DEBUG] Creating payment dialog for {plate}, {v_type}, {monthly_fee}")
        try:
            payment_dialog = PaymentDialog(plate, v_type, monthly_fee, self)
            print("[DEBUG] Payment dialog created successfully")
            result = payment_dialog.exec()
            print(f"[DEBUG] Dialog result: {result}, confirmed: {payment_dialog.payment_confirmed}")
            
            if result != QDialog.Accepted or not payment_dialog.payment_confirmed:
                QMessageBox.information(self, "Hủy", "Đăng ký vé tháng đã bị hủy")
                return
        except Exception as e:
            print(f"[ERROR] Payment dialog error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi", f"Lỗi hiển thị thanh toán: {e}")
            return
        
        # ✅ Chạy registration ASYNC để tránh block main thread
        print("[REGISTRATION] Starting async registration...")
        from threading import Thread
        registration_thread = Thread(
            target=self._do_register_monthly,
            args=(plate, owner, card, v_type, reg_date, exp_date, payment_dialog.payment_method),
            daemon=True
        )
        registration_thread.start()

    def _do_register_monthly(self, plate, owner, card, v_type, reg_date, exp_date, payment_method):
        """Thực hiện đăng ký vé tháng trên background thread"""
        try:
            from PySide6.QtCore import QMetaObject, Qt
            
            monthly_fee = 500000 if v_type == "Ô tô" else 200000
            print(f"\n[REGISTRATION] ========== STARTING REGISTRATION ==========")
            print(f"[REGISTRATION] Plate: {plate}, Owner: {owner}, Card: {card}, Type: {v_type}")
            print(f"[REGISTRATION] RegDate: {reg_date}, ExpDate: {exp_date}")
            
            # Step 1: Find available slot
            print(f"[REGISTRATION] Step 1: Finding available slot for {v_type} (is_monthly=True)...")
            assigned_slot = self.db.find_available_slot(v_type, is_monthly=True)
            print(f"[REGISTRATION] Step 1 Result: Slot = {assigned_slot}")
            
            # Step 2: Get avatar path
            avatar_path = self.selected_avatar_path if hasattr(self, 'selected_avatar_path') else ""
            print(f"[REGISTRATION] Step 2: Avatar path = {avatar_path}")
            
            # Step 3: Add to database
            print(f"[REGISTRATION] Step 3: Adding to database...")
            success, msg = self.db.add_monthly_ticket(plate, owner, card, v_type, reg_date, exp_date, assigned_slot, avatar_path)
            print(f"[REGISTRATION] Step 3 Result: success={success}, msg={msg}")
            
            if not success:
                print(f"[REGISTRATION] ❌ Database error: {msg}")
                # ✅ Invoke from main thread
                self._pending_error_msg = msg
                QMetaObject.invokeMethod(self, "_show_monthly_error_dialog", Qt.QueuedConnection)
                return
            
            # Step 4: Verify in database
            print(f"[REGISTRATION] Step 4: Verifying registration in database...")
            ticket_info = self.db.get_monthly_ticket_info(card)
            print(f"[REGISTRATION] Step 4 Result: ticket_info = {ticket_info}")
            
            if not ticket_info:
                print(f"[REGISTRATION] ⚠️ WARNING: Ticket not found in database after insertion!")
            
            # Step 5: Show success message - ✅ invoke from main thread
            print(f"[REGISTRATION] Step 5: Showing success message from main thread...")
            self._pending_registration_data = {
                'plate': plate,
                'owner': owner,
                'v_type': v_type,
                'assigned_slot': assigned_slot,
                'monthly_fee': monthly_fee,
                'payment_method': payment_method
            }
            QMetaObject.invokeMethod(self, "_show_monthly_success_dialog", Qt.QueuedConnection)
            
            # Step 6: Clear form from main thread
            print(f"[REGISTRATION] Step 6: Clearing form...")
            page = self.loaded_pages.get("monthly")
            if page:
                self._pending_page = page
                QMetaObject.invokeMethod(self, "_clear_monthly_form", Qt.QueuedConnection)
            
            # Step 7: Refresh UI after 1000ms from main thread
            print(f"[REGISTRATION] Step 7: Scheduling UI refresh after 1000ms...")
            from PySide6.QtCore import QTimer
            QMetaObject.invokeMethod(self, "_schedule_monthly_refresh", Qt.QueuedConnection)
            
            print(f"[REGISTRATION] ========== REGISTRATION COMPLETE ==========\n")
        except Exception as e:
            print(f"[REGISTRATION-ERROR] ❌ Exception occurred: {e}")
            import traceback
            traceback.print_exc()
            self._pending_error_msg = str(e)
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(self, "_show_monthly_error_dialog", Qt.QueuedConnection)

    def _show_monthly_success_dialog(self):
        """Called from main thread to show success dialog"""
        data = self._pending_registration_data
        QMessageBox.information(self, "Thành công", 
            f"✅ Đã đăng ký vé tháng thành công!\n\n"
            f"Biển số: {data['plate']}\n"
            f"Chủ xe: {data['owner']}\n"
            f"Loại xe: {data['v_type']}\n"
            f"Ô đỗ: {data['assigned_slot'] if data['assigned_slot'] else 'Vãng lai'}\n"
            f"Phí: {data['monthly_fee']:,} VND\n"
            f"Phương thức: {data['payment_method']}")

    def _show_monthly_error_dialog(self):
        """Called from main thread to show error dialog"""
        msg = self._pending_error_msg
        QMessageBox.critical(self, "Lỗi", f"❌ {msg}")

    def _clear_monthly_form(self):
        """Called from main thread to clear form"""
        page = self._pending_page
        page.findChild(QLineEdit, "newPlate").clear()
        page.findChild(QLineEdit, "newOwner").clear()
        page.findChild(QLineEdit, "newCardNumber").clear()
        self.selected_avatar_path = ""  # Reset ảnh đã chọn

    def _schedule_monthly_refresh(self):
        """Called from main thread to schedule refresh"""
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self.refresh_after_monthly_registration)

    def refresh_after_monthly_registration(self):
        """Refresh UI sau khi đăng kí vé tháng (gọi async)"""
        try:
            print("[REFRESH] Starting refresh_after_monthly_registration...")
            self.load_monthly_tickets()
            print("[REFRESH] ✅ load_monthly_tickets() completed")
            self.draw_parking_map()
            print("[REFRESH] ✅ draw_parking_map() completed")
            self.send_idle_lcd_message()
            print("[REFRESH] ✅ send_idle_lcd_message() completed")
        except Exception as e:
            print(f"[REFRESH-ERROR] {e}")
            import traceback
            traceback.print_exc()

    def handle_upload_avatar(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Chọn ảnh đại diện', '.', 'Image files (*.jpg *.png)')
        if fname:
            # Lưu đường dẫn ảnh vào biến tạm
            self.selected_avatar_path = fname
            QMessageBox.information(self, "Ảnh", f"Đã chọn: {os.path.basename(fname)}")
    
    def view_member_avatar(self, card_id):
        """Xem ảnh đại diện của thành viên theo mã thẻ"""
        avatar_path = self.db.get_member_avatar(card_id)
        
        if not avatar_path or not os.path.exists(avatar_path):
            QMessageBox.warning(self, "Không có ảnh", f"Chưa có ảnh đại diện cho thẻ: {card_id}")
            return
        
        # Tạo dialog hiển thị ảnh
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ảnh đại diện - Thẻ: {card_id}")
        dialog.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # Label hiển thị ảnh
        img_label = QLabel()
        pixmap = QPixmap(avatar_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(450, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
            img_label.setAlignment(Qt.AlignCenter)
        else:
            img_label.setText("Không thể tải ảnh")
        
        layout.addWidget(img_label)
        
        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def handle_scan_card_monthly(self):
        """Xử lý quét thẻ RFID cho đăng ký vé tháng"""
        page = self.loaded_pages.get("monthly")
        if not page:
            return
        
        card_input = page.findChild(QLineEdit, "newCardNumber")
        if not card_input:
            return
        
        # Hiển thị dialog chờ quét thẻ
        dialog = QDialog(self)
        dialog.setWindowTitle("Quét thẻ RFID")
        dialog.resize(350, 150)
        dialog.setModal(False)  # Set non-modal để events có thể xử lý
        
        layout = QVBoxLayout()
        
        lbl_instruction = QLabel("Vui lòng đưa thẻ RFID vào đầu đọc...")
        lbl_instruction.setAlignment(Qt.AlignCenter)
        lbl_instruction.setStyleSheet("font-size: 12pt; padding: 20px;")
        layout.addWidget(lbl_instruction)
        
        lbl_status = QLabel("Đang chờ...")
        lbl_status.setAlignment(Qt.AlignCenter)
        lbl_status.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(lbl_status)
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(dialog.reject)
        layout.addWidget(btn_cancel)
        
        dialog.setLayout(layout)
        
        # Biến lưu kết quả quét
        scanned_card = {"uid": None, "lane": None}
        
        def on_card_scanned_temp(uid, lane):
            """Callback tạm thời khi quét được thẻ"""
            print(f"[MONTHLY] Card scanned: {uid} from lane {lane}")
            if uid:  # Bỏ qua nếu uid rỗng (CHECKOUT)
                scanned_card["uid"] = uid
                scanned_card["lane"] = lane
                lbl_status.setText(f"✅ Đã quét: {uid}")
                lbl_status.setStyleSheet("color: green; font-size: 10pt; font-weight: bold;")
                # Tự động đóng sau 1.5 giây
                QTimer.singleShot(1500, dialog.accept)
        
        # Kết nối tín hiệu với Direct connection để đảm bảo nhận signal ngay lập tức
        self.network_server.card_scanned.connect(on_card_scanned_temp, Qt.DirectConnection)
        
        print("[MONTHLY] Waiting for card scan...")
        result = dialog.exec()
        
        # Ngắt kết nối sau khi đóng dialog
        try:
            self.network_server.card_scanned.disconnect(on_card_scanned_temp)
        except Exception as e:
            print(f"[MONTHLY] Disconnect error: {e}")
        
        # Nếu quét thành công, điền vào ô input
        if scanned_card["uid"]:
            card_input.setText(scanned_card["uid"])
            print(f"[MONTHLY] Card filled: {scanned_card['uid']}")
            
            # 📺 Gửi LCD message sau khi quét thẻ xong (tránh timeout)
            self.send_idle_lcd_message()
            
            QMessageBox.information(self, "Thành công", f"✅ Đã quét thẻ: {scanned_card['uid']}")
        else:
            print("[MONTHLY] Scan cancelled or timeout")
            
            # 📺 Gửi LCD message khi hủy quét (tránh timeout)
            self.send_idle_lcd_message()
            
            QMessageBox.information(self, "Hủy", "Đã hủy quét thẻ")
    
    def handle_monthly_search(self, text):
        """Xử lý tìm kiếm vé tháng"""
        self.load_monthly_tickets(text.strip())
    
    def delete_monthly_ticket(self, card_id):
        """Xóa vé tháng (soft delete)"""
        reply = QMessageBox.question(
            self, 
            "Xác nhận xóa", 
            f"Bạn có chắc muốn xóa vé tháng của thẻ: {card_id}?\n\nThao tác này không thể hoàn tác!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_monthly_ticket(card_id)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                
                # Reset trạng thái thẻ để có thể sử dụng lại
                if self._last_processed_card == card_id:
                    self._last_processed_card = ""
                    print(f"[MAIN] ✅ Reset debounce flag cho thẻ {card_id}")
                
                self.load_monthly_tickets()  # Reload bảng
            else:
                QMessageBox.critical(self, "Lỗi", msg)
    
    def extend_monthly_ticket_dialog(self, card_id, current_exp_date):
        """Dialog gia hạn vé tháng"""
        from datetime import datetime, timedelta
        
        # Tạo dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Gia hạn vé tháng - Thẻ: {card_id}")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Thông tin hiện tại
        lbl_current = QLabel(f"📅 Ngày hết hạn hiện tại: {current_exp_date}")
        lbl_current.setStyleSheet("font-size: 11pt; padding: 10px;")
        layout.addWidget(lbl_current)
        
        # Chọn thời gian gia hạn
        lbl_extend = QLabel("🔄 Gia hạn thêm:")
        lbl_extend.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_extend)
        
        # Buttons gia hạn nhanh
        extend_options = QHBoxLayout()
        
        btn_1month = QPushButton("1 tháng")
        btn_1month.clicked.connect(lambda: self.confirm_extend(dialog, card_id, current_exp_date, 1))
        extend_options.addWidget(btn_1month)
        
        btn_3months = QPushButton("3 tháng")
        btn_3months.clicked.connect(lambda: self.confirm_extend(dialog, card_id, current_exp_date, 3))
        extend_options.addWidget(btn_3months)
        
        btn_6months = QPushButton("6 tháng")
        btn_6months.clicked.connect(lambda: self.confirm_extend(dialog, card_id, current_exp_date, 6))
        extend_options.addWidget(btn_6months)
        
        btn_1year = QPushButton("1 năm")
        btn_1year.clicked.connect(lambda: self.confirm_extend(dialog, card_id, current_exp_date, 12))
        extend_options.addWidget(btn_1year)
        
        layout.addLayout(extend_options)
        
        # Hoặc chọn ngày cụ thể
        lbl_custom = QLabel("Hoặc chọn ngày hết hạn mới:")
        lbl_custom.setStyleSheet("margin-top: 20px;")
        layout.addWidget(lbl_custom)
        
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        # Set ngày mặc định là hôm nay + 1 tháng
        try:
            current = datetime.strptime(current_exp_date, "%Y-%m-%d")
            new_date = current + timedelta(days=30)
            date_edit.setDate(QDate(new_date.year, new_date.month, new_date.day))
        except:
            date_edit.setDate(QDate.currentDate().addMonths(1))
        
        layout.addWidget(date_edit)
        
        # Buttons xác nhận
        btn_layout = QHBoxLayout()
        
        btn_confirm = QPushButton("✅ Xác nhận")
        btn_confirm.setStyleSheet("background-color: #10B981; color: white; padding: 8px;")
        btn_confirm.clicked.connect(lambda: self.confirm_extend_custom(dialog, card_id, date_edit.date().toString("yyyy-MM-dd")))
        btn_layout.addWidget(btn_confirm)
        
        btn_cancel = QPushButton("❌ Hủy")
        btn_cancel.setStyleSheet("padding: 8px;")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def confirm_extend(self, dialog, card_id, current_exp_date, months):
        """Xác nhận gia hạn với số tháng cụ thể"""
        from datetime import datetime, timedelta
        
        try:
            # Lấy thông tin vé tháng để tính phí
            ticket_info = self.db.get_ticket_detail(card_id)
            if not ticket_info:
                QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin vé tháng!")
                return
            
            plate = ticket_info['plate_number']
            vehicle_type = ticket_info['vehicle_type']
            
            # Tính ngày hết hạn mới
            current = datetime.strptime(current_exp_date, "%Y-%m-%d")
            # Nếu đã hết hạn, tính từ hôm nay
            if current < datetime.now():
                base_date = datetime.now()
            else:
                base_date = current
            
            # Thêm số tháng (xấp xỉ 30 ngày/tháng)
            new_exp_date = base_date + timedelta(days=30 * months)
            new_exp_str = new_exp_date.strftime("%Y-%m-%d")
            
            # Tính phí gia hạn dựa trên loại xe
            monthly_fee = 500000 if vehicle_type == "Ô tô" else 200000
            total_fee = monthly_fee * months
            
            # Hiển thị dialog thanh toán
            payment_dialog = PaymentDialog(plate, vehicle_type, total_fee, self)
            result = payment_dialog.exec()
            
            if result == QDialog.Accepted and payment_dialog.payment_confirmed:
                # Thanh toán thành công -> Gia hạn vé
                success, msg = self.db.extend_monthly_ticket(card_id, new_exp_str)
                if success:
                    QMessageBox.information(self, "Thành công", 
                        f"✅ {msg}\n\n"
                        f"Biển số: {plate}\n"
                        f"Loại xe: {vehicle_type}\n"
                        f"Gia hạn: {months} tháng\n"
                        f"Ngày hết hạn mới: {new_exp_str}\n"
                        f"Phí: {total_fee:,} VND\n"
                        f"Phương thức: {payment_dialog.payment_method}")
                    self.load_monthly_tickets()
                    dialog.accept()
                else:
                    QMessageBox.critical(self, "Lỗi", msg)
            else:
                QMessageBox.information(self, "Hủy", "Đã hủy gia hạn")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi gia hạn: {str(e)}")
    
    def confirm_extend_custom(self, dialog, card_id, new_exp_date):
        """Xác nhận gia hạn với ngày tùy chỉnh"""
        from datetime import datetime
        
        try:
            # Lấy thông tin vé tháng
            ticket_info = self.db.get_ticket_detail(card_id)
            if not ticket_info:
                QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin vé tháng!")
                return
            
            plate = ticket_info['plate_number']
            vehicle_type = ticket_info['vehicle_type']
            current_exp_date = ticket_info['exp_date']
            
            # Validate ngày mới phải sau ngày hiện tại
            new_date = datetime.strptime(new_exp_date, "%Y-%m-%d")
            if new_date <= datetime.now():
                QMessageBox.warning(self, "Cảnh báo", "Ngày hết hạn mới phải sau ngày hiện tại!")
                return
            
            # Tính số tháng gia hạn (xấp xỉ)
            current_date = datetime.strptime(current_exp_date, "%Y-%m-%d")
            if current_date < datetime.now():
                current_date = datetime.now()
            
            days_diff = (new_date - current_date).days
            months_approx = max(1, round(days_diff / 30))  # Tối thiểu 1 tháng
            
            # Tính phí
            monthly_fee = 500000 if vehicle_type == "Ô tô" else 200000
            total_fee = monthly_fee * months_approx
            
            # Hiển thị dialog thanh toán
            payment_dialog = PaymentDialog(plate, vehicle_type, total_fee, self)
            result = payment_dialog.exec()
            
            if result == QDialog.Accepted and payment_dialog.payment_confirmed:
                # Thanh toán thành công -> Gia hạn vé
                success, msg = self.db.extend_monthly_ticket(card_id, new_exp_date)
                if success:
                    QMessageBox.information(self, "Thành công", 
                        f"✅ {msg}\n\n"
                        f"Biển số: {plate}\n"
                        f"Loại xe: {vehicle_type}\n"
                        f"Ngày hết hạn mới: {new_exp_date}\n"
                        f"Phí: {total_fee:,} VND\n"
                        f"Phương thức: {payment_dialog.payment_method}")
                    self.load_monthly_tickets()
                    dialog.accept()
                else:
                    QMessageBox.critical(self, "Lỗi", msg)
            else:
                QMessageBox.information(self, "Hủy", "Đã hủy gia hạn")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi gia hạn: {str(e)}")

    # --- CÁC HÀM KHÁC ---
    def update_dashboard_stats(self):
        """Cập nhật thống kê dashboard từ database"""
        stats = self.db.get_parking_statistics()
        
        # Cập nhật số liệu thống kê
        if self.lbl_stat1_value:
            self.lbl_stat1_value.setText(str(stats['motor_parking']))
        if self.lbl_stat2_value:
            self.lbl_stat2_value.setText(str(stats['car_parking']))
        if self.lbl_stat3_value:
            self.lbl_stat3_value.setText(str(stats['total_in_today']))
        if self.lbl_stat4_value:
            self.lbl_stat4_value.setText(str(stats['total_out_today']))
        
        # Cập nhật chỗ trống dùng sensor + DB logic (smart parking)
        self.update_dashboard_with_sensor_data()

    def auto_refresh_dashboard(self):
        """Tự động refresh dashboard nếu đang ở trang dashboard"""
        try:
            # Chỉ refresh khi đang ở trang dashboard
            current_page = self.stacked_widget.currentWidget()
            if current_page == self.loaded_pages.get("dashboard"):
                self.update_dashboard_stats()
                self.draw_parking_map()
                # print("[AUTO-REFRESH] Dashboard updated")
        except Exception as e:
            print(f"[AUTO-REFRESH] Error: {e}")

    def load_initial_settings(self):
        app_title = self.db.get_setting("parking_name", "Hệ thống giữ xe")
        lbl_title = self.ui.findChild(QLabel, "appTitle")
        if lbl_title: lbl_title.setText(app_title)
    
    # --- LOGIC TRANG HISTORY ---
    
    def setup_history_page(self, widget):
        """Thiết lập các kết nối cho trang lịch sử"""
        # Nút áp dụng filter
        btn_apply = widget.findChild(QPushButton, "btnApplyFilter")
        if btn_apply:
            btn_apply.clicked.connect(self.load_history)
            print("[HISTORY] Button 'Áp dụng' đã kết nối")
        
        # Khởi tạo giá trị mặc định
        date_from = widget.findChild(QDateEdit, "historyDateFrom")
        date_to = widget.findChild(QDateEdit, "historyDateTo")
        if date_from:
            date_from.setDate(QDate.currentDate().addDays(-30))
            print(f"[HISTORY] Date from: {date_from.date().toString('yyyy-MM-dd')}")
        if date_to:
            date_to.setDate(QDate.currentDate())
            print(f"[HISTORY] Date to: {date_to.date().toString('yyyy-MM-dd')}")
        
        # Kết nối signal cho table item click
        table = widget.findChild(QTableWidget, "historyTable")
        if table:
            table.itemClicked.connect(self._on_history_image_clicked)
            print("[HISTORY] Table itemClicked signal connected")
        
        # Load dữ liệu ban đầu
        print("[HISTORY] Loading initial data...")
        self.load_history()
    
    # --- LOGIC TRANG PARKING MAP (SƠ ĐỒ BÃI ĐỖ XE REALTIME) ---
    
    def setup_parking_map_page(self, widget):
        """Thiết lập trang sơ đồ bãi đỗ xe với 10 slots realtime"""
        print("[PARKING-MAP] Initializing parking map page...")
        
        # Lưu tham chiếu các slots từ database
        self.parking_slots = []
        self.parking_slot_ids = []
        
        # Load tất cả slots từ database
        all_slots_from_db = self.db.get_all_parking_slots()
        
        for i, db_slot in enumerate(all_slots_from_db):
            slot_id, vehicle_type, is_reserved, status = db_slot
            slot_widget = widget.findChild(QPushButton, f"slot_{i+1}")
            if slot_widget:
                self.parking_slots.append(slot_widget)
                self.parking_slot_ids.append(slot_id)  # Lưu tên slot thực tế từ DB
                print(f"[PARKING-MAP] Slot {i+1} (ID: {slot_id}) found")
            else:
                print(f"[PARKING-MAP] ⚠️ Slot {i+1} NOT found")
        
        # Lưu tham chiếu labels
        self.lbl_parking_zone_title = widget.findChild(QLabel, "lblZoneTitle")
        self.lbl_parking_available_count = widget.findChild(QLabel, "lblAvailableCount")
        
        # Cập nhật lần đầu
        self.update_parking_map_realtime()
    
    def update_parking_map_realtime(self):
        """Cập nhật màu sắc của 10 slots dựa trên dữ liệu sensor realtime"""
        if not hasattr(self, 'parking_slots') or len(self.parking_slots) == 0:
            print("[PARKING-MAP] ⚠️ Parking slots not initialized yet")
            return
        
        # Lấy binary status từ sensor manager
        binary_status = self.sensor_manager.current_binary_status
        
        print(f"[PARKING-MAP] Updating with binary: {binary_status}")
        
        # Màu sắc
        color_available = "background-color: #22c55e; color: white; font-size: 14pt; font-weight: 600; border-radius: 8px;"  # Xanh lá
        color_occupied = "background-color: #3b82f6; color: white; font-size: 14pt; font-weight: 600; border-radius: 8px;"   # Xanh lam
        
        occupied_count = 0
        available_count = 0
        
        # Cập nhật từng slot (binary_status có 10 ký tự: 0=trống, 1=có xe)
        for i in range(len(self.parking_slots)):
            slot_widget = self.parking_slots[i]
            
            # Lấy status từ binary string (nếu không đủ 10 ký tự, mặc định là available)
            if i < len(binary_status):
                status_char = binary_status[i]
                is_occupied = (status_char == '1')
            else:
                is_occupied = False
            
            if is_occupied:
                # Có xe - màu xanh lam
                slot_widget.setStyleSheet(f"QPushButton {{ {color_occupied} }}")
                occupied_count += 1
            else:
                # Chỗ trống - màu xanh lá
                slot_widget.setStyleSheet(f"QPushButton {{ {color_available} }}")
                available_count += 1
            
            # Cập nhật text với tên slot thực tế từ database
            slot_name = self.parking_slot_ids[i] if i < len(self.parking_slot_ids) else f"Slot {i+1}"
            slot_widget.setText(slot_name)
        
        # Cập nhật thông tin zone
        if self.lbl_parking_zone_title:
            self.lbl_parking_zone_title.setText("Khu vực: Bãi xe máy (Zone 1)")
        
        if self.lbl_parking_available_count:
            self.lbl_parking_available_count.setText(f"Chỗ trống: {available_count}/10")
            # Đổi màu dựa trên số chỗ trống
            if available_count > 5:
                self.lbl_parking_available_count.setStyleSheet("font-size:12pt; color:#22c55e; font-weight:600; padding: 5px;")
            elif available_count > 2:
                self.lbl_parking_available_count.setStyleSheet("font-size:12pt; color:#f59e0b; font-weight:600; padding: 5px;")
            else:
                self.lbl_parking_available_count.setStyleSheet("font-size:12pt; color:#ef4444; font-weight:600; padding: 5px;")
        
        print(f"[PARKING-MAP] ✅ Updated: {available_count} available, {occupied_count} occupied")
    
    # --- END PARKING MAP LOGIC ---
    
    def save_capture_image(self, qimage, capture_type="entry"):
        """Lưu ảnh chụp từ camera thành file và trả về đường dẫn"""
        try:
            import os
            from datetime import datetime
            
            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists("reports/images"):
                os.makedirs("reports/images", exist_ok=True)
            
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"reports/images/{capture_type}_{timestamp}.jpg"
            
            # Chuyển QImage thành file
            pixmap = QPixmap.fromImage(qimage)
            if pixmap.save(filename):
                print(f"[IMAGE-SAVE] ✅ Lưu ảnh thành công: {filename}")
                return filename
            else:
                print(f"[IMAGE-SAVE] ❌ Không thể lưu ảnh: {filename}")
                return None
        except Exception as e:
            print(f"[IMAGE-SAVE] ❌ Lỗi: {e}")
            return None
    
    def load_history(self):
        """Load và hiển thị lịch sử giao dịch"""
        print("[HISTORY] load_history() được gọi")
        page = self.loaded_pages.get("history")
        if not page:
            print("[HISTORY] ❌ Không tìm thấy page 'history'")
            return
        
        table = page.findChild(QTableWidget, "historyTable")
        if not table:
            print("[HISTORY] ❌ Không tìm thấy widget 'historyTable'")
            return
        
        print("[HISTORY] ✅ Widget historyTable tìm thấy")
        header = table.horizontalHeader()
        # Thiết lập headers ngay từ đầu
        headers = ["STT", "Mã thẻ", "Biển số", "Loại xe", "Ô đỗ", 
                   "Giờ vào", "Giờ ra", "Thời gian đỗ", "Loại vé", "Chủ xe",
                   "Phí", "Thanh toán", "Trạng thái", "Ảnh vào/ra"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # Thiết lập styling cho header
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                border: none;
                border-right: 1px solid #1a252f;
                font-weight: bold;
                height: 40px;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:alternate {
                background-color: #f9f9f9;
            }
        """)
        # Styling cho vertical header (STT) - bỏ màu xanh đậm
        table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: white;
                color: #333;
                padding: 5px;
                border: none;
                border-right: 1px solid #e0e0e0;
            }
        """)
        table.horizontalHeader().setVisible(True)
        table.verticalHeader().setVisible(True)  # Giữ hiển thị STT
        table.verticalHeader().setDefaultSectionSize(70)
        
        # Set resize mode cho tất cả columns
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Cài đặt column width cho cột ảnh (cột thứ 13)
        table.setColumnWidth(13, 100)  # Width 100 để hiển thị nút "Xem ảnh"
        
        # Cho phép alternating colors
        table.setAlternatingRowColors(True)
        
        print("[HISTORY] ✅ Headers đã được thiết lập")
        print(f"[HISTORY] Header visible: {table.horizontalHeader().isVisible()}")
        print(f"[HISTORY] Header height: {table.horizontalHeader().height()}")
        
        # Lấy thông tin filter
        plate = page.findChild(QLineEdit, "historyPlate")
        date_from = page.findChild(QDateEdit, "historyDateFrom")
        date_to = page.findChild(QDateEdit, "historyDateTo")
        
        plate_filter = plate.text().strip() if plate else ""
        date_from_str = date_from.date().toString("yyyy-MM-dd") if date_from else None
        date_to_str = date_to.date().toString("yyyy-MM-dd") if date_to else None
        
        # Lấy dữ liệu từ database (Lấy cả xe đang đỗ và xe đã ra)
        print(f"[HISTORY] Filters: plate='{plate_filter}', date={date_from_str} to {date_to_str}")
        history = self.db.get_parking_history(
            plate=plate_filter if plate_filter else None,
            date_from=date_from_str,
            date_to=date_to_str,
            status=None  # Không filter theo status - hiển thị tất cả (PARKING + PAID)
        )
        
        # Lưu dữ liệu toàn bộ và reset trang
        self._history_all_data = history
        self._history_current_page = 0
        self._history_rows_per_page = 10
        
        # Kết nối các nút pagination
        btn_prev = page.findChild(QPushButton, "btnPrevPage")
        btn_next = page.findChild(QPushButton, "btnNextPage")
        
        if btn_prev:
            print(f"[HISTORY] ✅ Found btnPrevPage: {btn_prev}")
            btn_prev.setEnabled(True)  # Ensure button is enabled initially
            try:
                btn_prev.clicked.disconnect()
            except Exception as e:
                print(f"[HISTORY] Note: {e}")
                pass
            btn_prev.clicked.connect(self._history_prev_page)
            print("[HISTORY] ✅ Connected btnPrevPage")
        else:
            print("[HISTORY] ❌ NOT found btnPrevPage")
            
        if btn_next:
            print(f"[HISTORY] ✅ Found btnNextPage: {btn_next}")
            btn_next.setEnabled(True)  # Ensure button is enabled initially
            try:
                btn_next.clicked.disconnect()
            except Exception as e:
                print(f"[HISTORY] Note: {e}")
                pass
            btn_next.clicked.connect(self._history_next_page)
            print("[HISTORY] ✅ Connected btnNextPage")
        else:
            print("[HISTORY] ❌ NOT found btnNextPage")
        
        # Hiển thị trang đầu tiên
        self._display_history_page()
        
        print(f"[HISTORY] ✅ Tìm thấy {len(history)} bản ghi")
    
    def _display_history_page(self):
        """Hiển thị trang hiện tại của lịch sử"""
        page = self.loaded_pages.get("history")
        if not page:
            return
        
        table = page.findChild(QTableWidget, "historyTable")
        if not table:
            return
        
        # Kiểm tra dữ liệu
        if not hasattr(self, '_history_all_data') or not self._history_all_data:
            table.setRowCount(0)
            return
        
        # Tính toán vị trí dữ liệu cho trang hiện tại
        start_idx = self._history_current_page * self._history_rows_per_page
        end_idx = start_idx + self._history_rows_per_page
        page_data = self._history_all_data[start_idx:end_idx]
        
        # Chỉ cần set số dòng, headers đã được thiết lập trong load_history()
        table.setRowCount(len(page_data))
        
        # Set row height để hiển thị nút đẹp (50px)
        for row_idx in range(len(page_data)):
            table.setRowHeight(row_idx, 50)
        
        print(f"[HISTORY-PAGE] Hiển thị trang {self._history_current_page + 1}, dòng {start_idx}-{end_idx}, dữ liệu: {len(page_data)} bản ghi")
        
        for row_idx, row_data in enumerate(page_data):
            # row_data indices (theo query get_history_parking_sessions):
            # 0:id, 1:card_id, 2:plate_in, 3:time_in, 4:time_out,
            # 5:slot_id, 6:vehicle_type, 7:ticket_type, 8:owner_name, 9:price,
            # 10:payment_method, 11:status, 12:image_in_path, 13:image_out_path,
            # 14:duration_hours, 15:duration_minutes
            
            # Tính toán trạng thái hiển thị
            status = row_data[11]  # status column (chỉnh từ 12 → 11)
            time_out = row_data[4]  # time_out column (chỉnh từ 5 → 4)
            
            if status == "PAID" and time_out:
                status_display = "🚪 Đã ra"
                status_color = "#22c55e"  # Green
            elif status == "PARKING":
                status_display = "🅿️ Đang đỗ"
                status_color = "#3b82f6"  # Blue
            else:
                status_display = "⏳ Đang xử lý"
                status_color = "#f59e0b"  # Orange
            
            # Tính thời gian đỗ
            duration_hours = int(row_data[14]) if row_data[14] is not None else 0  # Chỉnh từ 15 → 14
            duration_minutes = int(row_data[15]) if row_data[15] is not None else 0  # Chỉnh từ 16 → 15
            if row_data[4]:  # Chỉ hiển thị nếu có time_out (chỉnh từ [5] → [4])
                duration_display = f"{duration_hours}h {duration_minutes}m"
            else:
                duration_display = "-"
            
            # Map dữ liệu vào các cột
            display_data = [
                str(row_data[0]),                      # ID
                str(row_data[1]) if row_data[1] else "-",  # Mã thẻ
                str(row_data[2]) if row_data[2] else "-",  # Biển số (biển vào)
                str(row_data[6]) if row_data[6] else "-",  # Loại xe (chỉnh từ [7] → [6])
                str(row_data[5]) if row_data[5] else "-",  # Ô đỗ (slot_id - chỉnh từ [6] → [5])
                str(row_data[3]) if row_data[3] else "-",  # Giờ vào (chỉnh từ [4] → [3])
                str(row_data[4]) if row_data[4] else "-",  # Giờ ra (chỉnh từ [5] → [4])
                duration_display,                      # Thời gian đỗ
                str(row_data[7]) if row_data[7] else "-",  # Loại vé (chỉnh từ [8] → [7])
                str(row_data[8]) if row_data[8] else "-",  # Chủ xe/owner_name (chỉnh từ [9] → [8])
                f"{int(row_data[9]):,} VND" if row_data[9] else "0 VND",  # Phí (chỉnh từ [10] → [9])
                str(row_data[10]) if row_data[10] else "-",  # Thanh toán/payment_method (chỉnh từ [11] → [10])
                status_display,                        # Trạng thái (custom)
                row_data[12]  # Ảnh vào (chỉnh từ [13] → [12])
            ]
            
            for col_idx, display_val in enumerate(display_data):
                # Xử lý cột ảnh (cột 13 - index 13)
                if col_idx == 13:  # Cột ảnh
                    if display_val and display_val != "-":
                        # Hiển thị nút "Xem ảnh" thay vì thumbnail
                        has_image_in = display_val and os.path.exists(display_val)
                        has_image_out = row_data[13] and os.path.exists(row_data[13])
                        
                        if has_image_in or has_image_out:
                            # Tạo nút "Xem ảnh"
                            btn = QPushButton("📷 Xem ảnh")
                            btn.setStyleSheet("""
                                QPushButton {
                                    background-color: #3b82f6;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    padding: 5px 10px;
                                    font-weight: bold;
                                    font-size: 11px;
                                }
                                QPushButton:hover {
                                    background-color: #2563eb;
                                }
                                QPushButton:pressed {
                                    background-color: #1d4ed8;
                                }
                            """)
                            
                            # Lưu dữ liệu ảnh vào button để sử dụng khi click
                            image_in_path = row_data[12]
                            image_out_path = row_data[13]
                            
                            # Tạo lambda để capture các biến đúng
                            btn.clicked.connect(lambda checked=False, img_in=image_in_path, img_out=image_out_path: 
                                              self._show_history_images(img_in, img_out))
                            
                            table.setCellWidget(row_idx, col_idx, btn)
                        else:
                            item = QTableWidgetItem("❌")
                            table.setItem(row_idx, col_idx, item)
                    else:
                        item = QTableWidgetItem("-")
                        table.setItem(row_idx, col_idx, item)
                else:
                    item = QTableWidgetItem(str(display_val) if display_val else "")
                    
                    # Thêm màu cho cột trạng thái
                    if col_idx == 12:  # Cột trạng thái
                        item.setForeground(QColor(status_color))
                    
                    table.setItem(row_idx, col_idx, item)
        
        # Cập nhật thông tin pagination
        self._update_pagination_info()
        
        # Set header resize mode
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)
    
    def _on_history_image_clicked(self, item: QTableWidgetItem):
        """Xử lý sự kiện click vào ảnh trong bảng lịch sử"""
        col = item.column()

        # Cột ảnh = 13 (chỉ xử lý khi click vào cột ảnh)
        if col != 13:
            return

        data = item.data(Qt.UserRole)
        
        # Kiểm tra xem data có phải là tuple (image_in, image_out) hay không
        if isinstance(data, tuple) and len(data) == 2:
            image_in_path, image_out_path = data
            self._show_history_images(image_in_path, image_out_path)
        elif isinstance(data, str):
            # Trường hợp đơn giản - chỉ có 1 ảnh
            if os.path.exists(data):
                self._show_full_image(data)
    
    def _show_history_images(self, image_in_path, image_out_path):
        """Hiển thị ảnh vào/ra trong cùng một dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ảnh vào / Ảnh ra")
        dialog.setMinimumSize(900, 450)

        layout = QHBoxLayout(dialog)

        # ===== ẢNH VÀO =====
        in_layout = QVBoxLayout()
        lbl_in_title = QLabel("Ảnh vào")
        lbl_in_title.setAlignment(Qt.AlignCenter)
        lbl_in_title.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")

        lbl_in_img = QLabel()
        lbl_in_img.setAlignment(Qt.AlignCenter)
        lbl_in_img.setMinimumHeight(350)
        lbl_in_img.setMinimumWidth(400)

        if image_in_path and os.path.exists(image_in_path):
            pix = QPixmap(image_in_path).scaled(
                400, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_in_img.setPixmap(pix)
        else:
            lbl_in_img.setText("Không có ảnh vào")
            lbl_in_img.setStyleSheet("color: #999; font-size: 11px;")

        in_layout.addWidget(lbl_in_title)
        in_layout.addWidget(lbl_in_img, 1)

        # ===== ẢNH RA =====
        out_layout = QVBoxLayout()
        lbl_out_title = QLabel("Ảnh ra")
        lbl_out_title.setAlignment(Qt.AlignCenter)
        lbl_out_title.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")

        lbl_out_img = QLabel()
        lbl_out_img.setAlignment(Qt.AlignCenter)
        lbl_out_img.setMinimumHeight(350)
        lbl_out_img.setMinimumWidth(400)

        if image_out_path and os.path.exists(image_out_path):
            pix = QPixmap(image_out_path).scaled(
                400, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_out_img.setPixmap(pix)
        else:
            lbl_out_img.setText("Chưa có ảnh ra")
            lbl_out_img.setStyleSheet("color: #999; font-size: 11px;")

        out_layout.addWidget(lbl_out_title)
        out_layout.addWidget(lbl_out_img, 1)

        layout.addLayout(in_layout)
        layout.addLayout(out_layout)

        # Nút đóng
        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Đóng")
        btn_close.setMinimumWidth(100)
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout, 1)
        main_layout.addLayout(btn_layout)

        dialog.setLayout(main_layout)
        dialog.exec()
    
    def _update_pagination_info(self):
        """Cập nhật thông tin số trang và kích hoạt/vô hiệu hóa nút"""
        page = self.loaded_pages.get("history")
        if not page:
            return
        
        if not hasattr(self, '_history_all_data'):
            return
        
        total_records = len(self._history_all_data)
        total_pages = (total_records + self._history_rows_per_page - 1) // self._history_rows_per_page
        
        # Cập nhật label thông tin trang
        pagination_label = page.findChild(QLabel, "paginationLabel")
        if pagination_label:
            start_idx = self._history_current_page * self._history_rows_per_page + 1
            end_idx = min((self._history_current_page + 1) * self._history_rows_per_page, total_records)
            pagination_label.setText(f"Hiển thị {start_idx}-{end_idx} của {total_records} kết quả (Trang {self._history_current_page + 1}/{total_pages})")
        
        # Vô hiệu hóa nút prev/next
        btn_prev = page.findChild(QPushButton, "btnPrevPage")
        btn_next = page.findChild(QPushButton, "btnNextPage")
        
        prev_enabled = self._history_current_page > 0
        next_enabled = self._history_current_page < total_pages - 1
        
        if btn_prev:
            btn_prev.setEnabled(prev_enabled)
            print(f"[HISTORY] btnPrevPage enabled: {prev_enabled}")
        else:
            print("[HISTORY] ❌ Cannot find btnPrevPage in _update_pagination_info()")
            
        if btn_next:
            btn_next.setEnabled(next_enabled)
            print(f"[HISTORY] btnNextPage enabled: {next_enabled}")
        else:
            print("[HISTORY] ❌ Cannot find btnNextPage in _update_pagination_info()")
        
        print(f"[HISTORY] Current: {self._history_current_page + 1}/{total_pages}, Records: {total_records}")
    
    def _history_prev_page(self):
        """Chuyển sang trang trước"""
        print(f"[HISTORY-BTN] Prev button clicked! Current page: {self._history_current_page}")
        if self._history_current_page > 0:
            self._history_current_page -= 1
            self._display_history_page()
            print(f"[HISTORY-PAGE] ✅ Chuyển sang trang {self._history_current_page + 1}")
        else:
            print(f"[HISTORY-PAGE] ⚠️ Đã ở trang đầu tiên, không thể quay lại")
    
    def _history_next_page(self):
        """Chuyển sang trang sau"""
        print(f"[HISTORY-BTN] Next button clicked! Current page: {self._history_current_page}")
        if not hasattr(self, '_history_all_data'):
            print("[HISTORY-BTN] ❌ No history data")
            return
        total_pages = (len(self._history_all_data) + self._history_rows_per_page - 1) // self._history_rows_per_page
        if self._history_current_page < total_pages - 1:
            self._history_current_page += 1
            self._display_history_page()
            print(f"[HISTORY-PAGE] ✅ Chuyển sang trang {self._history_current_page + 1}")
        else:
            print(f"[HISTORY-PAGE] ⚠️ Đã ở trang cuối cùng ({total_pages}), không thể tiếp tục")
    
    def refresh_history_if_visible(self):
        page = self.loaded_pages.get("history")
        if not page:
            return

        if self.stacked_widget.currentWidget() == page:
            print("[HISTORY] 🔄 Auto refresh history")
            self.load_history()


    def closeEvent(self, event):
        """Dọn dẹp khi đóng ứng dụng"""
        print("[APP] Đang đóng ứng dụng...")
        
        # Dừng camera threads
        if self.camera_entry_thread: 
            self.camera_entry_thread.stop()
        if self.camera_exit_thread: 
            self.camera_exit_thread.stop()
        
        # Dừng network server
        if hasattr(self, 'network_server'):
            self.network_server.stop()
        
        event.accept()
        print("[APP] Đã đóng hoàn tất!")

    # --- STATISTICS PAGE ---
    def setup_statistics_page(self, widget):
        """Khởi tạo trang thống kê với các control"""
        # Tìm các widget
        self.stat_btn_today = widget.findChild(QPushButton, "btnFilterToday")
        self.stat_btn_month = widget.findChild(QPushButton, "btnFilterMonth")
        self.stat_btn_year = widget.findChild(QPushButton, "btnFilterYear")
        self.stat_date_from = widget.findChild(QDateEdit, "dateFrom")
        self.stat_date_to = widget.findChild(QDateEdit, "dateTo")
        self.stat_btn_apply = widget.findChild(QPushButton, "btnApplyFilter")
        
        # Summary labels
        self.stat_lbl_revenue = widget.findChild(QLabel, "totalRevenueLabel")
        self.stat_lbl_visits = widget.findChild(QLabel, "totalVisitsLabel")
        self.stat_lbl_split = widget.findChild(QLabel, "vehicleSplitLabel")
        self.stat_lbl_tickets = widget.findChild(QLabel, "ticketSplitLabel")
        
        # Chart labels (để draw matplotlib)
        self.stat_chart_revenue = widget.findChild(QLabel, "revenueChart")
        self.stat_chart_vehicles = widget.findChild(QLabel, "vehicleCountChart")
        self.stat_chart_pie_vehicle = widget.findChild(QLabel, "pieVehicleChart")
        self.stat_chart_pie_ticket = widget.findChild(QLabel, "pieTicketChart")
        
        # Set default dates
        from datetime import datetime, timedelta
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        self.stat_date_from.setDate(month_ago)
        self.stat_date_to.setDate(today)
        
        # Connect buttons
        if self.stat_btn_today:
            self.stat_btn_today.clicked.connect(self.on_stat_today)
        if self.stat_btn_month:
            self.stat_btn_month.clicked.connect(self.on_stat_month)
        if self.stat_btn_year:
            self.stat_btn_year.clicked.connect(self.on_stat_year)
        if self.stat_btn_apply:
            self.stat_btn_apply.clicked.connect(self.on_stat_apply)
        
        # Load initial data
        self.on_stat_month()
    
    def on_stat_today(self):
        from datetime import datetime
        today = datetime.now().date()
        self.stat_date_from.setDate(today)
        self.stat_date_to.setDate(today)
        self.on_stat_apply()
    
    def on_stat_month(self):
        from datetime import datetime, timedelta
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        self.stat_date_from.setDate(month_ago)
        self.stat_date_to.setDate(today)
        self.on_stat_apply()
    
    def on_stat_year(self):
        from datetime import datetime, timedelta
        today = datetime.now().date()
        year_ago = today - timedelta(days=365)
        self.stat_date_from.setDate(year_ago)
        self.stat_date_to.setDate(today)
        self.on_stat_apply()
    
    def on_stat_apply(self):
        """
        Hiển thị thống kê doanh thu & lượt xe (tự động theo ngày hoặc tháng)
        """
        try:
            import matplotlib.pyplot as plt
            from io import BytesIO
            from datetime import datetime

            date_from = self.stat_date_from.date().toString("yyyy-MM-dd")
            date_to = self.stat_date_to.date().toString("yyyy-MM-dd")

            # Auto-detect: nếu > 60 ngày thì group theo tháng, còn lại theo ngày
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            days_diff = (date_to_obj - date_from_obj).days
            is_month = days_diff > 60
            
            group_format = "%Y-%m" if is_month else "%Y-%m-%d"
            title_suffix = "tháng" if is_month else "ngày"

            rows = self.db.get_revenue_by_date_range(date_from, date_to)

            total_revenue = 0
            total_visits = 0
            motor_count = 0
            car_count = 0

            # Group data theo ngày hoặc tháng
            grouped_data = {}
            
            for row in rows:
                # row: (date, count, revenue, motor_count, car_count)
                total_revenue += row[2] or 0
                total_visits += row[1]
                motor_count += row[3] or 0
                car_count += row[4] or 0

                # Group key
                date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                key = date_obj.strftime(group_format)
                
                if key not in grouped_data:
                    grouped_data[key] = {"count": 0, "revenue": 0}
                
                grouped_data[key]["count"] += row[1]
                grouped_data[key]["revenue"] += row[2] or 0

            # Sắp xếp theo key (tự động theo ngày hoặc tháng)
            labels = sorted(grouped_data.keys())
            revenues = [grouped_data[label]["revenue"] for label in labels]
            visits = [grouped_data[label]["count"] for label in labels]

            # ===== UPDATE TEXT =====
            self.stat_lbl_revenue.setText(f"{int(total_revenue):,} đ")
            self.stat_lbl_visits.setText(str(total_visits))
            self.stat_lbl_split.setText(f"Xe máy: {motor_count} | Ô tô: {car_count}")


            # ===== BIỂU ĐỒ 1: DOANH THU =====
            if labels:
                fig, ax = plt.subplots(figsize=(6, 3), dpi=90)
                ax.plot(labels, revenues, marker='o', linewidth=2)
                ax.set_title(f"Doanh thu theo {title_suffix}")
                ax.set_ylabel("Doanh thu (đ)")
                ax.grid(alpha=0.3)
                ax.tick_params(axis='x', rotation=45)

                buf = BytesIO()
                fig.tight_layout()
                fig.savefig(buf, format="PNG")
                buf.seek(0)

                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                self.stat_chart_revenue.setPixmap(pix.scaledToWidth(400, Qt.SmoothTransformation))
                plt.close(fig)

            # ===== BIỂU ĐỒ 2: LƯỢT XE =====
            if labels:
                fig, ax = plt.subplots(figsize=(6, 3), dpi=90)
                ax.bar(labels, visits)
                ax.set_title(f"Lượt xe theo {title_suffix}")
                ax.set_ylabel("Số lượt")
                ax.grid(alpha=0.3, axis='y')
                ax.tick_params(axis='x', rotation=45)

                buf = BytesIO()
                fig.tight_layout()
                fig.savefig(buf, format="PNG")
                buf.seek(0)

                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                self.stat_chart_vehicles.setPixmap(pix.scaledToWidth(400, Qt.SmoothTransformation))
                plt.close(fig)

            # ===== BIỂU ĐỒ 3: PHÂN LOẠI XE =====
            if motor_count + car_count > 0:
                fig, ax = plt.subplots(figsize=(4, 4), dpi=90)
                ax.pie(
                    [motor_count, car_count],
                    labels=["Xe máy", "Ô tô"],
                    autopct="%1.1f%%",
                    startangle=90
                )
                ax.set_title("Tỷ lệ phương tiện")

                buf = BytesIO()
                fig.tight_layout()
                fig.savefig(buf, format="PNG")
                buf.seek(0)

                pix = QPixmap()
                pix.loadFromData(buf.getvalue())
                self.stat_chart_pie_vehicle.setPixmap(pix.scaledToWidth(300, Qt.SmoothTransformation))
                plt.close(fig)

            print(f"[STATS] OK | Revenue={total_revenue}, Visits={total_visits}")

        except Exception as e:
            print(f"[STATS-ERROR] {e}")


    # --- SETTINGS PAGE ---
    def setup_settings_page(self, widget):
        """Khởi tạo trang cài đặt"""
        # General tab
        self.set_parking_name = widget.findChild(QLineEdit, "parkingName")
        self.set_address = widget.findChild(QLineEdit, "address")
        self.set_phone = widget.findChild(QLineEdit, "phone")
        self.set_email = widget.findChild(QLineEdit, "email")
        self.set_btn_save_general = widget.findChild(QPushButton, "saveGeneral")
        
        # Pricing tab
        self.set_motor_first = widget.findChild(QLineEdit, "motor_first")
        self.set_motor_next = widget.findChild(QLineEdit, "motor_next")
        self.set_motor_max = widget.findChild(QLineEdit, "motor_max")
        self.set_car_first = widget.findChild(QLineEdit, "car_first")
        self.set_car_next = widget.findChild(QLineEdit, "car_next")
        self.set_car_max = widget.findChild(QLineEdit, "car_max")
        self.set_monthly_motor = widget.findChild(QLineEdit, "monthly_motor")
        self.set_monthly_car = widget.findChild(QLineEdit, "monthly_car")
        self.set_btn_save_pricing = widget.findChild(QPushButton, "savePricing")
        
        # Users tab
        self.set_new_username = widget.findChild(QLineEdit, "newUsername")
        self.set_new_password = widget.findChild(QLineEdit, "newPassword")
        self.set_new_fullname = widget.findChild(QLineEdit, "newFullName")
        self.set_new_role = widget.findChild(QComboBox, "newRole")
        self.set_btn_add_user = widget.findChild(QPushButton, "btnAddUser")
        self.set_users_table = widget.findChild(QTableWidget, "usersTable")
        
        # Permissions group (để chứa các checkbox quyền)
        self.set_permissions_layout = None
        
        # Connect buttons
        if self.set_btn_save_general:
            self.set_btn_save_general.clicked.connect(self.on_save_general_settings)
        if self.set_btn_save_pricing:
            self.set_btn_save_pricing.clicked.connect(self.on_save_pricing)
        if self.set_btn_add_user:
            self.set_btn_add_user.clicked.connect(self.on_add_user)
        
        # Load data
        self.load_all_settings()
    
    def load_all_settings(self):
        """Tải tất cả cài đặt từ DB"""
        try:
            # Load general settings
            parking_name = self.db.get_setting('parking_name', 'Bãi xe thông minh')
            address = self.db.get_setting('address', '')
            phone = self.db.get_setting('phone', '')
            email = self.db.get_setting('email', '')
            
            if self.set_parking_name:
                self.set_parking_name.setText(parking_name)
            if self.set_address:
                self.set_address.setText(address)
            if self.set_phone:
                self.set_phone.setText(phone)
            if self.set_email:
                self.set_email.setText(email)
            
            # Load pricing
            if self.set_motor_first:
                self.set_motor_first.setText(self.db.get_setting('price_xe_máy_block1', '5000'))
            if self.set_motor_next:
                self.set_motor_next.setText(self.db.get_setting('price_xe_máy_block2', '3000'))
            if self.set_motor_max:
                self.set_motor_max.setText(self.db.get_setting('price_xe_máy_max', '25000'))
            if self.set_car_first:
                self.set_car_first.setText(self.db.get_setting('price_ô_tô_block1', '25000'))
            if self.set_car_next:
                self.set_car_next.setText(self.db.get_setting('price_ô_tô_block2', '10000'))
            if self.set_car_max:
                self.set_car_max.setText(self.db.get_setting('price_ô_tô_max', '100000'))
            if self.set_monthly_motor:
                self.set_monthly_motor.setText(self.db.get_setting('price_xe_máy_monthly', '150000'))
            if self.set_monthly_car:
                self.set_monthly_car.setText(self.db.get_setting('price_ô_tô_monthly', '1200000'))
            
            # Load users
            self.reload_users_table()
            
        except Exception as e:
            print(f"[SETTINGS-ERROR] Lỗi load: {e}")
    
    def on_save_general_settings(self):
        """Lưu cài đặt chung và cập nhật ngay trong app"""
        try:
            self.db.save_setting('parking_name', self.set_parking_name.text())
            self.db.save_setting('address', self.set_address.text())
            self.db.save_setting('phone', self.set_phone.text())
            self.db.save_setting('email', self.set_email.text())
            
            # Cập nhật ngay lập tức trong giao diện
            parking_name = self.set_parking_name.text()
            self.setWindowTitle(parking_name)
            
            # Cập nhật appTitle nếu có
            lbl_title = self.ui.findChild(QLabel, "appTitle")
            if lbl_title:
                lbl_title.setText(parking_name)
            
            QMessageBox.information(self, "Thành công", "✅ Đã lưu cài đặt!\nThay đổi áp dụng ngay lập tức.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"❌ Lỗi lưu: {e}")
    
    def on_save_pricing(self):
        """Lưu bảng giá và cập nhật ngay lập tức"""
        try:
            self.db.save_setting('price_xe_máy_block1', self.set_motor_first.text())
            self.db.save_setting('price_xe_máy_block2', self.set_motor_next.text())
            self.db.save_setting('price_xe_máy_max', self.set_motor_max.text())
            self.db.save_setting('price_ô_tô_block1', self.set_car_first.text())
            self.db.save_setting('price_ô_tô_block2', self.set_car_next.text())
            self.db.save_setting('price_ô_tô_max', self.set_car_max.text())
            self.db.save_setting('price_xe_máy_monthly', self.set_monthly_motor.text())
            self.db.save_setting('price_ô_tô_monthly', self.set_monthly_car.text())
            
            QMessageBox.information(self, "Thành công", "✅ Đã lưu bảng giá!\nThay đổi áp dụng ngay lập tức cho các giao dịch mới.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"❌ Lỗi lưu: {e}")
    
    def on_add_user(self):
        """Thêm người dùng mới"""
        try:
            username = self.set_new_username.text().strip()
            password = self.set_new_password.text().strip()
            fullname = self.set_new_fullname.text().strip()
            role = "ADMIN" if self.set_new_role.currentIndex() == 1 else "STAFF"
            
            if not username or not password:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu!")
                return
            
            success, message = self.db.add_user(username, password, fullname, role)
            
            if success:
                # Lấy ID của user vừa tạo
                new_user = self.db.get_user_by_username(username)
                if new_user:
                    user_id = new_user[0]
                    # Nếu là STAFF, mở dialog chọn quyền (sẽ reload sau khi đóng dialog)
                    if role == "STAFF":
                        self.show_permissions_dialog(user_id)
                        # Reload sau khi đóng dialog
                        self.reload_users_table()
                    else:
                        # ADMIN tự động có tất cả quyền
                        self.db.set_user_permissions(user_id, list(self.db.AVAILABLE_PERMISSIONS.keys()))
                        # Reload ngay
                        self.reload_users_table()
                
                QMessageBox.information(self, "Thành công", f"✅ Đã thêm người dùng {username}!")
                self.set_new_username.clear()
                self.set_new_password.clear()
                self.set_new_fullname.clear()
            else:
                QMessageBox.critical(self, "Lỗi", f"❌ {message}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi: {e}")
    
    def reload_users_table(self):
        """Tải lại danh sách người dùng"""
        try:
            users = self.db.get_all_users()
            self.set_users_table.setRowCount(len(users))
            
            for row_idx, user in enumerate(users):
                user_id, username, fullname, role, is_active = user
                
                self.set_users_table.setItem(row_idx, 0, QTableWidgetItem(str(user_id)))
                self.set_users_table.setItem(row_idx, 1, QTableWidgetItem(username))
                self.set_users_table.setItem(row_idx, 2, QTableWidgetItem(fullname))
                self.set_users_table.setItem(row_idx, 3, QTableWidgetItem(role))
                
                # Action button
                btn_delete = QPushButton("Xóa")
                btn_delete.clicked.connect(lambda checked, uid=user_id: self.on_delete_user(uid))
                self.set_users_table.setCellWidget(row_idx, 4, btn_delete)
        except Exception as e:
            print(f"[USERS-ERROR] Lỗi reload: {e}")
    
    def on_delete_user(self, user_id):
        """Xóa người dùng"""
        if QMessageBox.question(self, "Xác nhận", "Xác nhận xóa người dùng?") == QMessageBox.Yes:
            if self.db.delete_user(user_id):
                self.reload_users_table()
    
    def show_permissions_dialog(self, user_id):
        """Hiển thị dialog chọn quyền cho nhân viên"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QCheckBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Phân quyền cho nhân viên")
        dialog.setGeometry(100, 100, 400, 350)
        
        layout = QVBoxLayout()
        
        # Nhóm quyền
        perm_group = QGroupBox("Các quyền hạn:", dialog)
        perm_layout = QVBoxLayout()
        
        checkboxes = {}
        current_permissions = self.db.get_user_permissions(user_id)
        
        for perm_code, perm_desc in self.db.AVAILABLE_PERMISSIONS.items():
            checkbox = QCheckBox(perm_desc)
            checkbox.setChecked(perm_code in current_permissions)
            checkboxes[perm_code] = checkbox
            perm_layout.addWidget(checkbox)
        
        perm_group.setLayout(perm_layout)
        layout.addWidget(perm_group)
        
        # Buttons
        btn_layout = QVBoxLayout()
        btn_save = QPushButton("Lưu quyền")
        btn_cancel = QPushButton("Hủy")
        
        def save_permissions():
            selected_perms = [code for code, cb in checkboxes.items() if cb.isChecked()]
            if self.db.set_user_permissions(user_id, selected_perms):
                QMessageBox.information(dialog, "Thành công", "Đã cập nhật quyền hạn!")
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "Lỗi", "Lỗi lưu quyền!")
        
        btn_save.clicked.connect(save_permissions)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def edit_user_permissions(self, user_id):
        """Chỉnh sửa quyền của nhân viên hiện tại"""
        self.show_permissions_dialog(user_id)

if __name__ == "__main__":
    # Đảm bảo đã chạy file database.py để khởi tạo DB
    init_db()  # Khởi tạo database nếu cần (sẽ skip nếu đã tồn tại)
    migrate_db()  # Cập nhật schema nếu có thay đổi
    app = QApplication(sys.argv)
    
    try:
        from config import UI_PATH
        style_path = os.path.join(UI_PATH, "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"Cảnh báo: Không tìm thấy file {style_path}")
    except ImportError:
        print("Lỗi: Không tìm thấy file config.py")

    # Hiển thị dialog đăng nhập
    login_dialog = LoginDialog()
    current_user = None
    current_role = None
    
    if login_dialog.exec() == QDialog.Accepted:
        # Lấy thông tin user đã đăng nhập
        current_user = login_dialog.username_input.text()
        current_role = None
        
        # Tạo main window
        window = MainWindow()
        
        # Cập nhật tiêu đề với thông tin user
        window.setWindowTitle(f"Smart Parking System - {current_user} ({current_role})")
        
        window.show()
        sys.exit(app.exec())
    else:
        # User hủy login
        print("Đã hủy đăng nhập")
        sys.exit(0)