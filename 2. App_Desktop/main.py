import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
                               QStackedWidget, QTableWidget, QTableWidgetItem, QLineEdit, 
                               QComboBox, QDateEdit, QFileDialog, QMessageBox)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QDate
from PySide6.QtGui import QPixmap

# Import các module core
from config import UI_PATH, PAGES_PATH, CAMERA_ENTRY_ID, CAMERA_EXIT_ID
from core.db_manager import DBManager
from core.camera_thread import CameraThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.camera_entry_thread = None
        self.camera_exit_thread = None
        
        # 1. Load giao diện chính
        self.ui = self.load_ui_file(os.path.join(UI_PATH, "app_mainwindow.ui"))
        if self.ui:
            self.setCentralWidget(self.ui.centralWidget())
            
        self.setWindowTitle("Hệ thống Quản lý Bãi đỗ xe J97")
        self.resize(1280, 800)

        # 2. Setup các trang con (Pages)
        self.setup_pages()

        # 3. Setup Menu bên trái (Sidebar)
        self.setup_sidebar()

        # 4. Khởi động Camera (nếu có)
        self.start_cameras()

        # 5. Load cấu hình ban đầu
        self.load_initial_settings()

    def load_ui_file(self, path):
        loader = QUiLoader()
        file = QFile(path)
        if not file.open(QFile.ReadOnly):
            print(f"Lỗi: Không thể mở file UI: {path}")
            return None
        window = loader.load(file)
        file.close()
        return window

    def setup_pages(self):
        """Load từng file .ui con vào trong QStackedWidget"""
        self.stacked_widget = self.findChild(QStackedWidget, "stackedPages")
        
        if not self.stacked_widget:
            return

        self.pages = {
            "dashboard": "dashboard.ui",
            "search": "search.ui",
            "monthly": "monthly.ui",
            "history": "history.ui",
            "statistics": "statistics.ui",
            "settings": "settings.ui"
        }
        
        self.loaded_pages = {} 

        for key, filename in self.pages.items():
            page_path = os.path.join(PAGES_PATH, filename)
            if os.path.exists(page_path):
                page_widget = self.load_ui_file(page_path)
                if page_widget:
                    self.stacked_widget.addWidget(page_widget)
                    self.loaded_pages[key] = page_widget
                    
                    # Cấu hình riêng cho từng trang sau khi load xong
                    if key == "monthly":
                        self.setup_monthly_page(page_widget)
                    elif key == "dashboard":
                        # Load dữ liệu mẫu cho dashboard
                        self.update_dashboard_stats(page_widget)

        if "dashboard" in self.loaded_pages:
            self.stacked_widget.setCurrentWidget(self.loaded_pages["dashboard"])

    def setup_sidebar(self):
        sidebar = self.findChild(QWidget, "sidebar")
        buttons = {
            "btnDashboard": "dashboard",
            "btnSearch": "search",
            "btnMonthly": "monthly",
            "btnHistory": "history",
            "btnStatistics": "statistics",
            "btnSettings": "settings"
        }

        for btn_name, page_key in buttons.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.clicked.connect(lambda checked, k=page_key: self.switch_page(k))

    def switch_page(self, page_key):
        if page_key in self.loaded_pages:
            self.stacked_widget.setCurrentWidget(self.loaded_pages[page_key])
            self.update_active_button(page_key)
            
            # Refresh dữ liệu khi vào trang
            if page_key == "monthly":
                self.load_monthly_tickets()

    def update_active_button(self, active_key):
        buttons_map = {
            "dashboard": "btnDashboard",
            "search": "btnSearch",
            "monthly": "btnMonthly",
            "history": "btnHistory",
            "statistics": "btnStatistics",
            "settings": "btnSettings"
        }
        
        for key, btn_name in buttons_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.setProperty("active", str(key == active_key).lower())
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    # --- LOGIC TRANG VÉ THÁNG (MONTHLY) ---
    def setup_monthly_page(self, widget):
        """Kết nối các nút trong trang Vé tháng"""
        # Nút Đăng ký (Đồng ý)
        btn_submit = widget.findChild(QPushButton, "btnRegisterSubmit")
        if btn_submit:
            btn_submit.clicked.connect(self.handle_register_monthly)
            
        # Nút Tải ảnh (Avatar)
        btn_upload = widget.findChild(QPushButton, "btnUploadAvatar")
        if btn_upload:
            btn_upload.clicked.connect(self.handle_upload_avatar)
            
        # Set ngày mặc định (Ngày hiện tại và +30 ngày)
        date_reg = widget.findChild(QDateEdit, "newRegDate")
        date_exp = widget.findChild(QDateEdit, "newExpDate")
        if date_reg and date_exp:
            today = QDate.currentDate()
            date_reg.setDate(today)
            date_exp.setDate(today.addDays(30))
            
        # Load danh sách vé ban đầu
        self.load_monthly_tickets()

    def load_monthly_tickets(self):
        """Lấy dữ liệu từ DB đổ vào bảng monthlyTable"""
        page = self.loaded_pages.get("monthly")
        if not page: return
        
        table = page.findChild(QTableWidget, "monthlyTable")
        if not table: return
        
        # Lấy dữ liệu từ DB
        tickets = self.db.get_all_monthly_tickets()
        
        # Cấu hình bảng
        headers = ["Biển số", "Chủ xe", "Mã thẻ", "Loại xe", "Đăng ký", "Hết hạn", "Ô đỗ riêng"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(tickets))
        
        for row_idx, row_data in enumerate(tickets):
            # row_data format: (plate, owner, card, type, reg, exp, slot)
            for col_idx, val in enumerate(row_data):
                item = QTableWidgetItem(str(val) if val else "")
                table.setItem(row_idx, col_idx, item)

    def handle_register_monthly(self):
        """Xử lý khi bấm nút Đăng ký"""
        page = self.loaded_pages.get("monthly")
        
        # Lấy dữ liệu từ form
        plate = page.findChild(QLineEdit, "newPlate").text()
        owner = page.findChild(QLineEdit, "newOwner").text()
        card = page.findChild(QLineEdit, "newCardNumber").text()
        v_type_cb = page.findChild(QComboBox, "newType")
        v_type = v_type_cb.currentText() if v_type_cb else "Ô tô"
        
        reg_date = page.findChild(QDateEdit, "newRegDate").date().toString("yyyy-MM-dd")
        exp_date = page.findChild(QDateEdit, "newExpDate").date().toString("yyyy-MM-dd")
        
        # Tự động tìm 1 ô trống (demo)
        slot = self.db.find_available_slot(v_type)
        if not slot:
            QMessageBox.warning(self, "Hết chỗ", f"Không còn ô trống cố định nào cho {v_type}!")
            # Vẫn cho lưu nhưng không có slot riêng (hoặc return tùy logic bạn muốn)
            # return 
        
        # Gọi DB để lưu
        success, msg = self.db.add_monthly_ticket(plate, owner, card, v_type, reg_date, exp_date, slot)
        
        if success:
            QMessageBox.information(self, "Thành công", f"Đã thêm vé tháng!\nÔ đỗ chỉ định: {slot}")
            self.load_monthly_tickets() # Reload bảng
            # Clear form
            page.findChild(QLineEdit, "newPlate").clear()
            page.findChild(QLineEdit, "newOwner").clear()
            page.findChild(QLineEdit, "newCardNumber").clear()
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def handle_upload_avatar(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Chọn ảnh đại diện', '.', 'Image files (*.jpg *.png)')
        if fname:
            # Lưu đường dẫn ảnh vào biến tạm hoặc hiển thị preview (tạm thời chỉ thông báo)
            QMessageBox.information(self, "Ảnh", f"Đã chọn: {fname}")

    # --- CÁC HÀM KHÁC ---
    def update_dashboard_stats(self, dashboard_widget):
        # Demo set số liệu
        lbl = dashboard_widget.findChild(QLabel, "stat1_value")
        if lbl: lbl.setText("10") # Ví dụ cập nhật số thật từ DB sau này

    def start_cameras(self):
        dashboard = self.loaded_pages.get("dashboard")
        if dashboard:
            lbl_entry = dashboard.findChild(QLabel, "camEntryImage")
            if lbl_entry and CAMERA_ENTRY_ID is not None:
                self.camera_entry_thread = CameraThread(CAMERA_ENTRY_ID)
                self.camera_entry_thread.change_pixmap_signal.connect(lambda img: lbl_entry.setPixmap(QPixmap.fromImage(img)))
                self.camera_entry_thread.start()

            lbl_exit = dashboard.findChild(QLabel, "camExitImage")
            if lbl_exit and CAMERA_EXIT_ID is not None:
                if CAMERA_EXIT_ID != CAMERA_ENTRY_ID:
                    self.camera_exit_thread = CameraThread(CAMERA_EXIT_ID)
                    self.camera_exit_thread.change_pixmap_signal.connect(lambda img: lbl_exit.setPixmap(QPixmap.fromImage(img)))
                    self.camera_exit_thread.start()

    def load_initial_settings(self):
        app_title = self.db.get_setting("parking_name", "Hệ thống giữ xe")
        lbl_title = self.findChild(QLabel, "appTitle")
        if lbl_title: lbl_title.setText(app_title)

    def closeEvent(self, event):
        if self.camera_entry_thread: self.camera_entry_thread.stop()
        if self.camera_exit_thread: self.camera_exit_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style_path = os.path.join(UI_PATH, "styles_light.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())