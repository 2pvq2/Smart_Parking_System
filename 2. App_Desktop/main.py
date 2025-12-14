import sys
import os
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
                               QStackedWidget, QTableWidget, QTableWidgetItem, QLineEdit, 
                               QComboBox, QDateEdit, QFileDialog, QMessageBox, QGraphicsView, QGraphicsScene,
                               QProgressBar, QDialog, QVBoxLayout, QHBoxLayout, QTimeEdit, QSpinBox, QCheckBox)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDate, QTime, Qt, QRectF, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor, QBrush, QPen, QFont

# --- CẤU HÌNH IMPORT THEO CẤU TRÚC MỚI ---
# Thêm thư mục hiện tại (2. App_Desktop) vào sys.path để import các file ngang cấp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import UI_PATH, PAGES_PATH, CAMERA_ENTRY_ID, CAMERA_EXIT_ID, ENABLE_AI_DETECTION
from database import init_db # Import hàm init_db để khởi tạo DB
from core.db_manager import DBManager
from core.camera_thread import CameraThread
from core.network_server import NetworkServer
from core.sensor_manager import SensorDataManager

# --- CẤU HÌNH CHUNG CÓ THỂ THAY ĐỔI ---
MOTOR_SLOTS = 5  # Số slot xe máy
CAR_SLOTS = 5    # Số slot ô tô

# --- TÍNH PHÍ (Hàm độc lập) ---
# Tái định nghĩa hàm tính phí vì nó sử dụng DBManager (cần giữ logic này trong main)
def calculate_parking_fee(db: DBManager, vehicle_type: str, time_in_str: str, time_out_seconds: float):
    # ... (Logic hàm tính phí từ bước trước, sử dụng DBManager để lấy giá vé) ...
    try:
        time_in = time.mktime(time.strptime(time_in_str, "%Y-%m-%d %H:%M:%S"))
        parking_duration_minutes = (time_out_seconds - time_in) / 60
        
        if parking_duration_minutes < 0: return 0
        
        # Lấy giá từ settings
        price_key_1 = f"price_{vehicle_type.lower().replace(' ', '_')}_block1"
        price_key_2 = f"price_{vehicle_type.lower().replace(' ', '_')}_block2"
        
        price_block1 = int(db.get_setting(price_key_1, '25000')) # 25k/lượt đầu
        price_block2 = int(db.get_setting(price_key_2, '10000')) # 10k/giờ tiếp theo
        
        block1_minutes = 120
        fee = 0
        
        if parking_duration_minutes <= block1_minutes:
            fee = price_block1
        else:
            fee += price_block1
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
        
        # Timer tự động refresh dashboard mỗi 5 giây
        self.dashboard_refresh_timer = QTimer(self)
        self.dashboard_refresh_timer.timeout.connect(self.auto_refresh_dashboard)
        self.dashboard_refresh_timer.start(5000)  # 5000ms = 5 giây
        print("[INIT] ✅ Auto-refresh timer started (5s interval)")
        
        # Khởi tạo Network Server (kết nối với ESP32)
        self.network_server = NetworkServer(host='0.0.0.0', port=8888)
        # Sử dụng Qt.QueuedConnection cho cross-thread signal
        self.network_server.card_scanned.connect(self.on_esp_card_scanned, Qt.QueuedConnection)
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
        self.lbl_avail1_value = widget.findChild(QLabel, "avail1_value")  # Chỗ trống ô tô
        self.lbl_avail1_progress = widget.findChild(QProgressBar, "avail1_progress")
        self.lbl_avail2_value = widget.findChild(QLabel, "avail2_value")  # Chỗ trống xe máy
        self.lbl_avail2_progress = widget.findChild(QProgressBar, "avail2_progress")
        
        # Buttons barie và thanh toán
        self.btn_open_barrier_in = widget.findChild(QPushButton, "btnOpenBarrierIn")
        self.btn_open_barrier_out = widget.findChild(QPushButton, "btnOpenBarrierOut")
        self.btn_confirm_exit = widget.findChild(QPushButton, "btnConfirmExit")
        
        print(f"[DEBUG] latestEntry_plate found: {self.lbl_entry_plate is not None}")
        print(f"[DEBUG] latestExit_plate found: {self.lbl_exit_plate is not None}")
        print(f"[DEBUG] btnConfirmExit found: {self.btn_confirm_exit is not None}")
        
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
                session_id, plate_in, time_in, vehicle_type = last_entry
                vehicle_icon = "🏍️" if vehicle_type == "Xe máy" else "🚗"
                
                if self.lbl_entry_plate:
                    self.lbl_entry_plate.setText(f"{vehicle_icon} {plate_in} ({vehicle_type})")
                if self.lbl_entry_time:
                    self.lbl_entry_time.setText(f"Thời gian: {time_in}")
                    
                print(f"[STARTUP] ✅ Loaded last entry: {plate_in} at {time_in}")
            
            # Tải thông tin ra cuối cùng
            last_exit = self.db.get_last_exit_session()
            if last_exit:
                session_id, plate_out, time_out, price, payment_method = last_exit
                
                if self.lbl_exit_plate:
                    self.lbl_exit_plate.setText(f"🚗 {plate_out}")
                if self.lbl_exit_time_price:
                    fee_text = f"{price:,}đ" if price else "0đ"
                    self.lbl_exit_time_price.setText(f"Thời gian: {time_out} | Phí: {fee_text}")
                    
                print(f"[STARTUP] ✅ Loaded last exit: {plate_out} at {time_out}")
                
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
    
    def clear_exit_lane_after_timeout(self, seconds=3):
        """Clear exit lane info sau khi xe ra được N giây"""
        def clear():
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText("...")
                self.lbl_exit_plate.setStyleSheet("")
            if self.lbl_exit_time_price:
                self.lbl_exit_time_price.setText("")
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("")
        
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
            if self.txt_entry_rfid and self.txt_entry_rfid.text().strip():
                # Nếu đã có RFID, tự động kiểm tra
                self.handle_rfid_scan()
            else:
                # Chưa có RFID, hiển thị hướng dẫn
                if self.lbl_entry_guidance:
                    self.lbl_entry_guidance.setText(f"✅ {vehicle_icon} {vehicle_type} - Vui lòng quét thẻ RFID")
            
    def update_exit_lpr(self, plate_text):
        print(f"[DEBUG] update_exit_lpr called with: {plate_text}")
        
        # Lọc ra biển số hợp lệ
        if plate_text and plate_text != "..." and not plate_text.startswith("LỖI"):
            if self.lbl_exit_plate:
                # Cập nhật thông tin biển số ra
                self.lbl_exit_plate.setText(f"🚗 {plate_text}")
                print(f"[DEBUG] Exit plate updated: {plate_text}")
                
                # Cập nhật thời gian
                if self.lbl_exit_time_price:
                    from datetime import datetime
                    current_time = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
                    self.lbl_exit_time_price.setText(f"Thời gian: {current_time}")
            else:
                print("[DEBUG] lbl_exit_plate is None!")
                
            self.current_exit_plate = plate_text
            
            # Tự động tính phí khi nhận diện được biển số
            self.calculate_fee_and_display(plate_text)

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
    
    def on_sensor_data_received(self, zone_id, status_binary, occupied, available):
        """
        Nhận dữ liệu từ Node cảm biến
        
        Args:
            zone_id: ID của zone (1-10)
            status_binary: Binary string 10 ký tự (VD: "1010001101")
            occupied: Số slot có xe
            available: Số slot trống
        """
        print(f"[SENSOR-HANDLER] Zone {zone_id}: {status_binary} | "
              f"Occupied={occupied}, Available={available}")
        
        # Cập nhật sensor manager
        self.sensor_manager.update_from_node(zone_id, status_binary, occupied, available)
        
        # CHỈ update UI nếu binary status THAY ĐỔI
        if self._last_sensor_binary != status_binary:
            print(f"[SENSOR-CHANGE-DETECTED] Binary changed: {self._last_sensor_binary} → {status_binary}")
            self._last_sensor_binary = status_binary
            
            # Cập nhật dashboard
            self.update_dashboard_with_sensor_data()
            
            # Gửi thông tin cập nhật lên LCD
            self.send_idle_lcd_message()
        else:
            # Binary không đổi - KHÔNG update UI (giảm spam)
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
            # Kiểm tra timeout - reset nếu không có update từ sensor lâu quá
            if self.sensor_manager.check_sensor_timeout():
                print("[DASHBOARD-UPDATE] ⚠️ Sensor timeout, dữ liệu đã được reset")
            
            # Lấy stats từ DB
            stats = self.db.get_parking_statistics()
            
            # Lấy số xe đang parking từ DB
            motor_db_parking = stats['motor_total'] - stats['motor_available']
            car_db_parking = stats['car_total'] - stats['car_available']
            
            # Lấy binary status từ sensor (10 bits)
            sensor_binary = self.sensor_manager.sensor_data.get('status_binary', '0000000000')
            
            # Chia sensor thành 2 phần:
            # - Slot 0-4 (5 bits đầu): Xe máy
            # - Slot 5-9 (5 bits cuối): Ô tô
            motor_binary = sensor_binary[0:MOTOR_SLOTS]  # MOTOR_SLOTS bits đầu
            car_binary = sensor_binary[MOTOR_SLOTS:MOTOR_SLOTS+CAR_SLOTS]   # CAR_SLOTS bits cuối
            
            # Đếm số chỗ trống từ sensor
            motor_sensor_available = motor_binary.count('0')  # 0 = available
            car_sensor_available = car_binary.count('0')
            
            # Tính số chỗ trống theo DB
            motor_db_available = MOTOR_SLOTS - motor_db_parking
            car_db_available = CAR_SLOTS - car_db_parking
            
            # Chọn min (logic an toàn)
            motor_available_smart = min(motor_sensor_available, motor_db_available)
            car_available_smart = min(car_sensor_available, car_db_available)
            
            print(f"[DASHBOARD-UPDATE] Motor: sensor={motor_sensor_available}, db={motor_db_available}, result={motor_available_smart}")
            print(f"[DASHBOARD-UPDATE] Car: sensor={car_sensor_available}, db={car_db_available}, result={car_available_smart}")
            
            # ⚠️ Stat1 & Stat2 (số xe đang gửi) chỉ update từ DB khi có transaction
            # Không update ở đây để tránh fluctuation từ sensor
            # Chỉ update chỗ trống (dùng smart logic với sensor)
            # Cập nhật chỗ trống ô tô (dùng sensor + DB)
            if self.lbl_avail1_value:
                self.lbl_avail1_value.setText(f"{car_available_smart} / {CAR_SLOTS} chỗ")
                
                # Thêm indicator nếu có dữ liệu cảm biến fresh
                if self.sensor_manager.is_data_fresh():
                    self.lbl_avail1_value.setStyleSheet("color: #22c55e; font-weight: bold;")
                else:
                    self.lbl_avail1_value.setStyleSheet("")
            
            if self.lbl_avail1_progress:
                percentage = int((car_available_smart / CAR_SLOTS) * 100)
                self.lbl_avail1_progress.setValue(percentage)
            
            # Cập nhật chỗ trống xe máy (dùng sensor + DB)
            if self.lbl_avail2_value:
                self.lbl_avail2_value.setText(f"{motor_available_smart} / {MOTOR_SLOTS} chỗ")
                
                # Thêm indicator nếu có dữ liệu cảm biến fresh
                if self.sensor_manager.is_data_fresh():
                    self.lbl_avail2_value.setStyleSheet("color: #22c55e; font-weight: bold;")
                else:
                    self.lbl_avail2_value.setStyleSheet("")
            
            if self.lbl_avail2_progress:
                percentage = int((motor_available_smart / MOTOR_SLOTS) * 100)
                self.lbl_avail2_progress.setValue(percentage)
            
            # Cập nhật parking map (bất kể đang ở trang nào)
            if hasattr(self, 'parking_slots') and len(self.parking_slots) > 0:
                self.update_parking_map_realtime()
            
            print(f"[DASHBOARD-UPDATE] Motor: {motor_available_smart}/{stats['motor_total']}, "
                  f"Car: {car_available_smart}/{stats['car_total']}")
            
        except Exception as e:
            print(f"[DASHBOARD-ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    def send_idle_lcd_message(self):
        """Gửi LCD message idle state mỗi 10 giây"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            return
        
        try:
            # Lấy thống kê từ database
            stats = self.db.get_parking_statistics()
            if stats:
                # stats là dictionary, không phải tuple
                available_car = stats['car_available']
                available_motor = stats['motor_available']
                
                # Nếu có dữ liệu sensor fresh, dùng dữ liệu sensor thực tế
                if self.sensor_manager.is_data_fresh():
                    # Tính smart available từ sensor + DB
                    motor_db_parking = stats['motor_total'] - stats['motor_available']
                    car_db_parking = stats['car_total'] - stats['car_available']
                    smart_counts = self.sensor_manager.get_smart_available_count(motor_db_parking, car_db_parking)
                    available_car = smart_counts['car_available']
                    available_motor = smart_counts['motor_available']
                
                # Gửi lên LCD
                line1 = "SMART PARKING"
                line2 = f"OTO:{available_car} XM:{available_motor}"
                self.network_server.send_lcd_message(line1, line2)
                print(f"[ESP-LCD-IDLE] {line1} / {line2}")
        except Exception as e:
            print(f"[ESP] Lỗi gửi idle LCD: {e}")
    
    def send_slot_info_to_esp(self):
        """Gửi thông tin số chỗ trống xuống ESP32 với dữ liệu từ cảm biến"""
        if not hasattr(self, 'network_server') or not self.network_server.is_connected():
            return
        
        try:
            # Lấy thống kê từ database
            stats = self.db.get_parking_statistics()
            
            # Tính số chỗ trống thông minh cho từng loại
            motor_db_parking = stats['motor_total'] - stats['motor_available']
            car_db_parking = stats['car_total'] - stats['car_available']
            
            smart_counts = self.sensor_manager.get_smart_available_count(motor_db_parking, car_db_parking)
            motor_available = smart_counts['motor_available']
            car_available = smart_counts['car_available']
            
            # Gửi xuống ESP: SLOTS:car:motor
            cmd = f"SLOTS:{car_available}:{motor_available}"
            self.network_server.send_command(cmd)
            print(f"[ESP] Gửi slot info: Car={car_available}, Motor={motor_available}")
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
        self._last_processed_card = rfid
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
        
        if ticket_info:
            plate_db = ticket_info['plate_number']
            slot_db = ticket_info['assigned_slot']
            
            # Kiểm tra biển số có khớp không
            if self.current_entry_plate != "..." and self.current_entry_plate != plate_db:
                error_msg = f"Biển số không khớp! Thẻ {rfid}: {plate_db} ≠ Camera: {self.current_entry_plate}"
                self.display_entry_lane_error(error_msg, auto_clear_seconds=5)
                QMessageBox.warning(self, "Cảnh báo Vé tháng", 
                    f"Thẻ {rfid} của xe **{plate_db}** nhưng camera đọc: **{self.current_entry_plate}**! Kiểm tra lại.")
                self.lbl_entry_guidance.setText(f"⚠️ Biển số không khớp!")
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
        
        # Hiển thị ảnh vừa chụp lên UI
        dashboard = self.loaded_pages.get("dashboard")
        if dashboard:
            lbl_exit = dashboard.findChild(QLabel, "camExitImage")
            if lbl_exit:
                lbl_exit.setPixmap(QPixmap.fromImage(captured_image))
        
        # Cập nhật thông tin biển số và tính phí
        self.update_exit_lpr(plate_text)
    
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
        success = self.db.record_entry(card_id, plate, vehicle_type, assigned_slot, 'MONTHLY')
        
        if success:
            # Gửi thông tin lên LCD ESP32
            owner_name = ticket_info.get('owner_name', '')
            self.send_vehicle_info_to_lcd(plate, vehicle_type, assigned_slot, owner_name)
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            
            # Hiển thị thông báo ngắn
            self.lbl_entry_guidance.setText(f"✅ Vào tại: {assigned_slot} - 🚧 Barie đã mở")
            print(f"[AUTO] Khách tháng {plate} vào slot {assigned_slot}")
            
            # Cập nhật slot trên dashboard
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(assigned_slot)
            
            # Cập nhật slot info
            self.send_slot_info_to_esp()
            
            # Reset sau 3 giây
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.reset_entry_ui)
            
            # Cập nhật UI
            self.draw_parking_map()
            self.update_dashboard_stats()
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
            # Kiểm tra thông tin chi tiết
            stats = self.db.get_parking_statistics()
            if vehicle_type == "Ô tô":
                available = stats['car_available']
                total = stats['car_total']
            else:
                available = stats['motor_available']
                total = stats['motor_total']
            
            error_msg = f"❌ Bãi đầy! {vehicle_type}: {available}/{total} chỗ trống"
            print(f"[ENTRY ERROR] {error_msg}")
            self.lbl_entry_guidance.setText(error_msg)
            
            # Gửi thông báo lên LCD ESP32
            if self.network_server.is_connected():
                self.network_server.send_lcd_message("BAI DAY!", f"{vehicle_type}: {available}/{total}")
                print(f"[ESP-LCD] Đã gửi thông báo bãi đầy lên LCD")
            else:
                print(f"[ESP-LCD] ⚠️ ESP32 chưa kết nối, không thể gửi LCD")
            
            # Reset UI về trạng thái ban đầu sau 3 giây
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.reset_entry_ui)
            return
        
        # Ghi nhận xe vào
        success = self.db.record_entry(card_id, plate, vehicle_type, assigned_slot, ticket_type)
        
        if success:
            # Gửi thông tin lên LCD ESP32
            self.send_vehicle_info_to_lcd(plate, vehicle_type, assigned_slot)
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            
            # Hiển thị thông báo ngắn
            self.lbl_entry_guidance.setText(f"✅ Vãng lai vào tại: {assigned_slot} - 🚧 Barie đã mở")
            print(f"[AUTO] Khách vãng lai {plate} vào slot {assigned_slot}")
            
            # Cập nhật slot trên dashboard
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(assigned_slot)
            
            # Reset sau 3 giây
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.reset_entry_ui)
            
            # Cập nhật UI
            self.draw_parking_map()
            self.update_dashboard_stats()
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
        if self.lbl_entry_guidance:
            self.lbl_entry_guidance.setText("✅ Sẵn sàng quét thẻ...")
        
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
            
            # Tự động mở barie
            self.handle_open_barrier_in()
            
            QMessageBox.information(self, "Xe Vào Thành Công", f"Xe {plate} ({ticket_type}) đã đỗ tại {assigned_slot}.\n🚧 Barie đã mở!")
            self.lbl_entry_guidance.setText(f"✅ Đỗ tại: {assigned_slot}")
            
            # Cập nhật slot trên dashboard
            if self.lbl_entry_slot:
                self.lbl_entry_slot.setText(assigned_slot)
            
            self.txt_entry_rfid.clear()
            self.current_entry_plate = "..."
            if self.lbl_entry_plate:
                self.lbl_entry_plate.setText("...")
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
        
        # Kiểm tra vé tháng - MIỄN PHÍ
        if ticket_type == 'MONTHLY':
            self.lbl_exit_fee.setText("✅ VÉ THÁNG - MIỄN PHÍ")
            # Gửi info lên LCD
            self.send_vehicle_info_to_lcd(exit_plate, vehicle_type, slot_id, "VE THANG")
            # Tự động xử lý xe ra cho vé tháng
            self.auto_process_monthly_exit(exit_plate, session[0])
            return 0, session[0], session[3], 'MONTHLY'
        
        fee = calculate_parking_fee(self.db, vehicle_type, time_in_str, time.time())
        
        time_in = time.mktime(time.strptime(time_in_str, "%Y-%m-%d %H:%M:%S"))
        parking_duration_minutes = (time.time() - time_in) / 60
        
        self.lbl_exit_fee.setText(f"{fee:,} VND ({int(parking_duration_minutes)} phút)")
        
        # Gửi thông tin xe và phí lên LCD
        self.send_vehicle_info_to_lcd(exit_plate, vehicle_type, slot_id)
        self.send_fee_to_lcd(fee)
        
        return fee, session[0], session[3], ticket_type # fee, id, slot_id, ticket_type
    
    def auto_process_monthly_exit(self, plate, session_id):
        """Tự động xử lý xe vé tháng ra khỏi bãi"""
        success = self.db.record_exit(session_id, plate, 0, 'MONTHLY')
        
        if success:
            # Tự động mở barie
            self.handle_open_barrier_out()
            
            print(f"[AUTO] Khách tháng {plate} ra - Miễn phí")
            
            # Reset UI sau 3 giây
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.reset_exit_ui)
            
            # Cập nhật UI
            self.draw_parking_map()
            self.update_dashboard_stats()
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
        success = self.db.record_exit(session_id, exit_plate, fee, payment_method)
        
        if success:
            # Tự động mở barie
            self.handle_open_barrier_out()
            
            QMessageBox.information(self, "Xe Ra Thành Công", 
                f"✅ Đã thanh toán {fee:,} VND\n"
                f"Phương thức: {payment_method}\n"
                f"🚧 Barie đã mở!")
            
            # Clear exit lane info after 3 seconds (successful exit)
            self.clear_exit_lane_after_timeout(seconds=3)
            
            self.current_exit_plate = "..."
            if self.lbl_exit_plate:
                self.lbl_exit_plate.setText("...")
            if self.lbl_exit_fee:
                self.lbl_exit_fee.setText("0 VND")
            
            # Reset exit processing flag
            self._exit_processing = False
            
            self.draw_parking_map()
            self.update_dashboard_stats()  # Cập nhật thống kê
        else:
            error_msg = "Lỗi ghi nhận xe ra vào Database."
            self.display_exit_lane_error(error_msg, auto_clear_seconds=5)
            QMessageBox.critical(self, "Lỗi", error_msg)
            self._exit_processing = False
            
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
        
        # Khởi tạo biến lưu đường dẫn ảnh
        self.selected_avatar_path = ""
        
        # Load dữ liệu vé tháng ban đầu
        self.load_monthly_tickets()
    
    def load_monthly_tickets(self, search_query=""):
        page = self.loaded_pages.get("monthly")
        if not page: return
        table = page.findChild(QTableWidget, "monthlyTable")
        if not table: return
        
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
        
        # Thanh toán thành công -> Tạo vé tháng
        assigned_slot = self.db.find_available_slot(v_type, is_monthly=True) 
        
        # Lưu ảnh đại diện (nếu có)
        avatar_path = self.selected_avatar_path if hasattr(self, 'selected_avatar_path') else ""
        
        success, msg = self.db.add_monthly_ticket(plate, owner, card, v_type, reg_date, exp_date, assigned_slot, avatar_path)
        
        if success:
            QMessageBox.information(self, "Thành công", 
                f"✅ Đã đăng ký vé tháng thành công!\n\n"
                f"Biển số: {plate}\n"
                f"Chủ xe: {owner}\n"
                f"Loại xe: {v_type}\n"
                f"Ô đỗ: {assigned_slot if assigned_slot else 'Vãng lai'}\n"
                f"Phí: {monthly_fee:,} VND\n"
                f"Phương thức: {payment_dialog.payment_method}")
            
            self.load_monthly_tickets()
            page.findChild(QLineEdit, "newPlate").clear()
            page.findChild(QLineEdit, "newOwner").clear()
            page.findChild(QLineEdit, "newCardNumber").clear()
            self.selected_avatar_path = ""  # Reset ảnh đã chọn
            self.draw_parking_map() 
        else:
            QMessageBox.critical(self, "Lỗi", msg)

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
        scanned_card = {"uid": None}
        
        def on_card_scanned_temp(uid, lane):
            """Callback tạm thời khi quét được thẻ"""
            scanned_card["uid"] = uid
            lbl_status.setText(f"✅ Đã quét: {uid}")
            lbl_status.setStyleSheet("color: green; font-size: 10pt; font-weight: bold;")
            # Tự động đóng sau 1 giây
            QTimer.singleShot(1000, dialog.accept)
        
        # Kết nối tín hiệu tạm thời
        self.network_server.card_scanned.connect(on_card_scanned_temp, Qt.QueuedConnection)
        
        result = dialog.exec()
        
        # Ngắt kết nối sau khi đóng dialog
        try:
            self.network_server.card_scanned.disconnect(on_card_scanned_temp)
        except:
            pass
        
        # Nếu quét thành công, điền vào ô input
        if result == QDialog.Accepted and scanned_card["uid"]:
            card_input.setText(scanned_card["uid"])
            QMessageBox.information(self, "Thành công", f"Đã quét thẻ: {scanned_card['uid']}")
        elif result == QDialog.Rejected:
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
        
        # Cập nhật chỗ trống ô tô
        if self.lbl_avail1_value:
            self.lbl_avail1_value.setText(f"{stats['car_available']} / {stats['car_total']} chỗ")
        if self.lbl_avail1_progress:
            if stats['car_total'] > 0:
                percentage = int((stats['car_available'] / stats['car_total']) * 100)
                self.lbl_avail1_progress.setValue(percentage)
            else:
                self.lbl_avail1_progress.setValue(0)
        
        # Cập nhật chỗ trống xe máy
        if self.lbl_avail2_value:
            self.lbl_avail2_value.setText(f"{stats['motor_available']} / {stats['motor_total']} chỗ")
        if self.lbl_avail2_progress:
            if stats['motor_total'] > 0:
                percentage = int((stats['motor_available'] / stats['motor_total']) * 100)
                self.lbl_avail2_progress.setValue(percentage)
            else:
                self.lbl_avail2_progress.setValue(0)

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
        
        # Nút xuất Excel
        btn_export = widget.findChild(QPushButton, "btnExport")
        if btn_export:
            btn_export.clicked.connect(self.export_history)
            print("[HISTORY] Button 'Xuất Excel' đã kết nối")
        
        # Khởi tạo giá trị mặc định
        date_from = widget.findChild(QDateEdit, "historyDateFrom")
        date_to = widget.findChild(QDateEdit, "historyDateTo")
        if date_from:
            date_from.setDate(QDate.currentDate().addDays(-7))
            print(f"[HISTORY] Date from: {date_from.date().toString('yyyy-MM-dd')}")
        if date_to:
            date_to.setDate(QDate.currentDate())
            print(f"[HISTORY] Date to: {date_to.date().toString('yyyy-MM-dd')}")
        
        # Load dữ liệu ban đầu
        print("[HISTORY] Loading initial data...")
        self.load_history()
    
    # --- LOGIC TRANG PARKING MAP (SƠ ĐỒ BÃI ĐỖ XE REALTIME) ---
    
    def setup_parking_map_page(self, widget):
        """Thiết lập trang sơ đồ bãi đỗ xe với 10 slots realtime"""
        print("[PARKING-MAP] Initializing parking map page...")
        
        # Lưu tham chiếu các slots
        self.parking_slots = []
        for i in range(1, 11):
            slot = widget.findChild(QPushButton, f"slot_{i}")
            if slot:
                self.parking_slots.append(slot)
                print(f"[PARKING-MAP] Slot {i} found")
            else:
                print(f"[PARKING-MAP] ⚠️ Slot {i} NOT found")
        
        # Lưu tham chiếu labels
        self.lbl_parking_zone_title = widget.findChild(QLabel, "lblZoneTitle")
        self.lbl_parking_available_count = widget.findChild(QLabel, "lblAvailableCount")
        
        # Kết nối button test
        btn_test = widget.findChild(QPushButton, "btnTestColor")
        if btn_test:
            btn_test.clicked.connect(self.test_parking_map_color)
            print("[PARKING-MAP] Test button connected")
        
        # Cập nhật lần đầu
        self.update_parking_map_realtime()
    
    def test_parking_map_color(self):
        """Test thay đổi màu slots (simulate cảm biến)"""
        import random
        # Tạo binary status ngẫu nhiên
        test_binary = ''.join([str(random.randint(0, 1)) for _ in range(10)])
        print(f"[PARKING-MAP-TEST] 🧪 Testing with binary: {test_binary}")
        
        # Force update sensor manager với binary test
        self.sensor_manager.sensor_data['status_binary'] = test_binary
        
        # Trigger update màu
        self.update_parking_map_realtime()
        
        print(f"[PARKING-MAP-TEST] ✅ Colors should be updated now!")
    
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
            
            # Cập nhật text (giữ nguyên "Slot X")
            slot_widget.setText(f"Slot {i+1}")
        
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
        
        # Lấy thông tin filter
        plate = page.findChild(QLineEdit, "historyPlate")
        date_from = page.findChild(QDateEdit, "historyDateFrom")
        date_to = page.findChild(QDateEdit, "historyDateTo")
        time_from = page.findChild(QTimeEdit, "historyTimeFrom")
        time_to = page.findChild(QTimeEdit, "historyTimeTo")
        
        plate_filter = plate.text().strip() if plate else ""
        date_from_str = date_from.date().toString("yyyy-MM-dd") if date_from else None
        date_to_str = date_to.date().toString("yyyy-MM-dd") if date_to else None
        time_from_str = time_from.time().toString("HH:mm:ss") if time_from else "00:00:00"
        time_to_str = time_to.time().toString("HH:mm:ss") if time_to else "23:59:59"
        
        # Lấy dữ liệu từ database
        print(f"[HISTORY] Filters: plate='{plate_filter}', date={date_from_str} to {date_to_str}")
        history = self.db.get_parking_history(
            plate=plate_filter if plate_filter else None,
            date_from=date_from_str,
            date_to=date_to_str,
            time_from=time_from_str,
            time_to=time_to_str
        )
        
        print(f"[HISTORY] ✅ Tìm thấy {len(history)} bản ghi")
        
        # Định nghĩa headers
        # Row data: (id, card_id, plate_in, plate_out, time_in, time_out, 
        #            image_in_path, image_out_path, price, vehicle_type, 
        #            ticket_type, status, payment_method, slot_id)
        headers = ["ID", "Mã thẻ", "Biển vào", "Biển ra", "Giờ vào", "Giờ ra", 
                   "Trạng thái", "Loại xe", "Loại vé", "Phí", "Thanh toán", "Vị trí"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(history))
        
        print(f"[HISTORY] Đang hiển thị {len(history)} dòng vào bảng...")
        
        for row_idx, row_data in enumerate(history):
            # row_data indices:
            # 0:id, 1:card_id, 2:plate_in, 3:plate_out, 4:time_in, 5:time_out,
            # 6:image_in_path, 7:image_out_path, 8:price, 9:vehicle_type,
            # 10:ticket_type, 11:status, 12:payment_method, 13:slot_id
            
            # Tính toán trạng thái hiển thị
            status = row_data[11]  # status column
            time_out = row_data[5]  # time_out column
            
            if status == "PAID" and time_out:
                status_display = "🚪 Đã ra"
                status_color = "#22c55e"  # Green
            elif status == "PARKING":
                status_display = "🅿️ Đang đỗ"
                status_color = "#3b82f6"  # Blue
            else:
                status_display = "⏳ Đang xử lý"
                status_color = "#f59e0b"  # Orange
            
            # Map dữ liệu vào các cột
            display_data = [
                str(row_data[0]),                    # ID
                str(row_data[1]) if row_data[1] else "-",  # Mã thẻ
                str(row_data[2]) if row_data[2] else "-",  # Biển vào
                str(row_data[3]) if row_data[3] else "-",  # Biển ra
                str(row_data[4]) if row_data[4] else "-",  # Giờ vào
                str(row_data[5]) if row_data[5] else "-",  # Giờ ra
                status_display,                      # Trạng thái (custom)
                str(row_data[9]) if row_data[9] else "-",  # Loại xe
                str(row_data[10]) if row_data[10] else "-", # Loại vé
                f"{int(row_data[8]):,} VND" if row_data[8] else "0 VND",  # Phí
                str(row_data[12]) if row_data[12] else "-", # Thanh toán
                str(row_data[13]) if row_data[13] else "-"  # Vị trí
            ]
            
            for col_idx, display_val in enumerate(display_data):
                item = QTableWidgetItem(display_val)
                
                # Thêm màu cho cột trạng thái
                if col_idx == 6:  # Cột trạng thái
                    item.setForeground(QColor(status_color))
                
                table.setItem(row_idx, col_idx, item)
        
        # Resize columns
        table.resizeColumnsToContents()
        print("[HISTORY] ✅ Hiển thị hoàn tất")
    
    def export_history(self):
        """Xuất lịch sử ra file Excel"""
        fname, _ = QFileDialog.getSaveFileName(self, 'Xuất lịch sử', '.', 'Excel files (*.xlsx)')
        if fname:
            try:
                # TODO: Implement Excel export using openpyxl or pandas
                QMessageBox.information(self, "Xuất file", f"Sẽ xuất dữ liệu ra file: {fname}\n(Chức năng đang phát triển)")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {e}")

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
        """Tính toán và hiển thị thống kê"""
        try:
            date_from = self.stat_date_from.date().toString("yyyy-MM-dd")
            date_to = self.stat_date_to.date().toString("yyyy-MM-dd")
            
            rows = self.db.get_revenue_by_date_range(date_from, date_to)
            
            total_revenue = 0
            total_visits = 0
            motor_count = 0
            car_count = 0
            
            for row in rows:
                total_revenue += row[2] if row[2] else 0
                total_visits += row[1]
                motor_count += row[3] if row[3] else 0
                car_count += row[4] if row[4] else 0
            
            # Update labels
            if self.stat_lbl_revenue:
                self.stat_lbl_revenue.setText(f"{total_revenue:,}đ")
            if self.stat_lbl_visits:
                self.stat_lbl_visits.setText(str(total_visits))
            if self.stat_lbl_split:
                self.stat_lbl_split.setText(f"{motor_count} / {car_count}")
            
            print(f"[STATS] Doanh thu: {total_revenue}đ, Lượt xe: {total_visits}")
            
        except Exception as e:
            print(f"[STATS-ERROR] Lỗi: {e}")

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
                self.set_motor_first.setText(self.db.get_setting('price_motor_block1', '5000'))
            if self.set_motor_next:
                self.set_motor_next.setText(self.db.get_setting('price_motor_block2', '3000'))
            if self.set_motor_max:
                self.set_motor_max.setText(self.db.get_setting('price_motor_max', '25000'))
            if self.set_car_first:
                self.set_car_first.setText(self.db.get_setting('price_car_block1', '25000'))
            if self.set_car_next:
                self.set_car_next.setText(self.db.get_setting('price_car_block2', '10000'))
            if self.set_car_max:
                self.set_car_max.setText(self.db.get_setting('price_car_max', '100000'))
            if self.set_monthly_motor:
                self.set_monthly_motor.setText(self.db.get_setting('price_motor_monthly', '150000'))
            if self.set_monthly_car:
                self.set_monthly_car.setText(self.db.get_setting('price_car_monthly', '1200000'))
            
            # Load users
            self.reload_users_table()
            
        except Exception as e:
            print(f"[SETTINGS-ERROR] Lỗi load: {e}")
    
    def on_save_general_settings(self):
        """Lưu cài đặt chung"""
        try:
            self.db.save_setting('parking_name', self.set_parking_name.text())
            self.db.save_setting('address', self.set_address.text())
            self.db.save_setting('phone', self.set_phone.text())
            self.db.save_setting('email', self.set_email.text())
            
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi lưu: {e}")
    
    def on_save_pricing(self):
        """Lưu bảng giá"""
        try:
            self.db.save_setting('price_motor_block1', self.set_motor_first.text())
            self.db.save_setting('price_motor_block2', self.set_motor_next.text())
            self.db.save_setting('price_motor_max', self.set_motor_max.text())
            self.db.save_setting('price_car_block1', self.set_car_first.text())
            self.db.save_setting('price_car_block2', self.set_car_next.text())
            self.db.save_setting('price_car_max', self.set_car_max.text())
            self.db.save_setting('price_motor_monthly', self.set_monthly_motor.text())
            self.db.save_setting('price_car_monthly', self.set_monthly_car.text())
            
            QMessageBox.information(self, "Thành công", "Đã lưu bảng giá!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi lưu: {e}")
    
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
            
            if self.db.add_user(username, password, fullname, role):
                # Lấy ID của user vừa tạo
                new_user = self.db.get_user_by_username(username)
                if new_user:
                    user_id = new_user[0]
                    # Nếu là STAFF, mở dialog chọn quyền
                    if role == "STAFF":
                        self.show_permissions_dialog(user_id)
                    else:
                        # ADMIN tự động có tất cả quyền
                        self.db.set_user_permissions(user_id, list(self.db.AVAILABLE_PERMISSIONS.keys()))
                
                QMessageBox.information(self, "Thành công", f"Đã thêm người dùng {username}!")
                self.set_new_username.clear()
                self.set_new_password.clear()
                self.set_new_fullname.clear()
                self.reload_users_table()
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể thêm người dùng (username đã tồn tại?)")
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
    # init_db() # Gọi hàm khởi tạo nếu cần
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

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())