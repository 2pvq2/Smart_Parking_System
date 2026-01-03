#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login Dialog - Xác thực người dùng (Admin/Nhân viên)
Load giao diện từ file .ui
"""
import sys
import os
from PySide6.QtWidgets import (QDialog, QApplication, QLineEdit, QPushButton, 
                               QCheckBox, QLabel, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer, QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QFont

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import hash_password
from core.db_manager import DBManager

class LoginDialog(QDialog):
    """Dialog đăng nhập với hỗ trợ Admin và Nhân viên"""
    
    # Signal phát ra khi đăng nhập thành công
    login_success = Signal(str, str)  # (username, role)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBManager()
        # ⚡ Bỏ: self.selected_role (role sẽ lấy từ database sau khi login)
        self.failed_attempts = 0
        self.login_in_progress = False  # Flag để ngăn gọi login() nhiều lần
        # self.max_attempts = 5  # Đã bỏ giới hạn số lần đăng nhập thất bại
        
        # Load UI từ file .ui
        self.load_ui()
        
        # Kiểm tra nếu chưa có tài khoản admin, tạo mặc định
        self.init_default_accounts()
    
    def load_ui(self):
        """Load giao diện từ file .ui"""
        ui_file = os.path.join(os.path.dirname(__file__), "ui", "login_dialog.ui")
        
        if not os.path.exists(ui_file):
            print(f"[ERROR] Cannot find file: {ui_file}")
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy file giao diện: {ui_file}")
            self.reject()
            return
        
        try:
            loader = QUiLoader()
            ui_file_obj = QFile(ui_file)
            
            if not ui_file_obj.open(QFile.ReadOnly):
                print(f"[ERROR] Cannot open file: {ui_file}")
                self.reject()
                return
            
            # Load widget từ file .ui
            widget = loader.load(ui_file_obj, self)
            ui_file_obj.close()
            
            if not widget:
                print("[ERROR] UI load error")
                self.reject()
                return
            
            print(f"[OK] UI loaded from: {ui_file}")
            
            # Lấy tất cả widgets từ loaded widget
            self.setWindowTitle(widget.windowTitle())
            self.setModal(widget.isModal())
            self.setMinimumSize(widget.minimumSize())
            
            # Move layout từ loaded widget sang dialog
            if widget.layout():
                self.setLayout(widget.layout())
            
            # Kết nối các UI elements
            self.setup_connections()
            
        except Exception as e:
            print(f"[ERROR] UI load error: {e}")
            self.reject()
    
    def setup_connections(self):
        """Kết nối signals từ các UI elements"""
        try:
            # Find widgets
            self.username_input = self.findChild(QLineEdit, "username_input")
            self.password_input = self.findChild(QLineEdit, "password_input")
            self.login_button = self.findChild(QPushButton, "login_button")
            self.exit_button = self.findChild(QPushButton, "exit_button")
            self.remember_checkbox = self.findChild(QCheckBox, "remember_checkbox")
            self.show_password_checkbox = self.findChild(QCheckBox, "show_password_checkbox")
            self.status_label = self.findChild(QLabel, "status_label")
            
            # Validate widgets exist (bỏ admin_btn, staff_btn)
            if not all([self.username_input, self.password_input, self.login_button, 
                       self.exit_button]):
                print("[ERROR] Some UI elements not found")
                return
            
            # Connect signals
            self.login_button.clicked.connect(self.login)
            self.exit_button.clicked.connect(self.reject)
            # ⚡ Bỏ: admin_btn.clicked, staff_btn.clicked (không chọn role ở giao diện)
            
            if self.show_password_checkbox:
                self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
            
            self.username_input.returnPressed.connect(self.login)
            self.password_input.returnPressed.connect(self.login)
            
            # ⚡ Bỏ: select_role (role sẽ lấy từ database)
            
            # Load remembered username
            self.load_remembered_username()
            
            print("[OK] UI connected successfully")
        
        except Exception as e:
            print(f"[ERROR] UI connection error: {e}")
    
    def toggle_password_visibility(self):
        """Bật/tắt hiển thị mật khẩu"""
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def init_default_accounts(self):
        """Tạo tài khoản mặc định (admin) nếu chưa có"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    admin_password = hash_password("admin123")
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, role, phone, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("admin", admin_password, "Quản trị viên", "ADMIN", "0000000000", 1))
                    
                    staff_password = hash_password("staff123")
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, role, phone, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("staff1", staff_password, "Nhân viên 1", "STAFF", "0123456789", 1))
                    
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, role, phone, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("staff2", staff_password, "Nhân viên 2", "STAFF", "0987654321", 1))
                    
                    conn.commit()
                    print("[OK] Default accounts created:")
                    print("  Admin: admin / admin123")
                    print("  Staff1: staff1 / staff123")
                    print("  Staff2: staff2 / staff123")
            
        except Exception as e:
            print(f"[ERROR] Account init error: {e}")
    
    def login(self):
        """Xác thực đăng nhập"""
        # Ngăn gọi login() nhiều lần
        if self.login_in_progress:
            return
        
        self.login_in_progress = True
        
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            error_msg = "❌ Vui lòng nhập tên đăng nhập và mật khẩu"
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Lỗi đăng nhập", error_msg))
            # Reset flag sau 1 giây
            QTimer.singleShot(1000, lambda: setattr(self, 'login_in_progress', False))
            return
        
    
        try:
            print(f"[LOGIN] Attempting login for: {username}")
            with self.db.connect() as conn:
                cursor = conn.cursor()
                # ⚡ Query chỉ cần username, role sẽ lấy từ database
                cursor.execute("""
                    SELECT id, username, password, role, full_name, is_active 
                    FROM users 
                    WHERE username = ?
                """, (username,))
                
                user = cursor.fetchone()
            
            if user is None:
                self.failed_attempts += 1
                error_msg = f"❌ Tên đăng nhập không tồn tại"
                print(f"[LOGIN] User not found: {username}")
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Lỗi đăng nhập", error_msg))
                # Reset flag sau 1 giây
                QTimer.singleShot(1000, lambda: setattr(self, 'login_in_progress', False))
                return
            
            user_id, user_name, hashed_password, role, full_name, is_active = user
            
            if hash_password(password) != hashed_password:
                self.failed_attempts += 1
                error_msg = f"❌ Mật khẩu không chính xác"
                print(f"[LOGIN] Wrong password for: {username}")
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Lỗi đăng nhập", error_msg))
                # Reset flag sau 1 giây
                QTimer.singleShot(1000, lambda: setattr(self, 'login_in_progress', False))
                return
            
            
            self.failed_attempts = 0
            
            if self.remember_checkbox and self.remember_checkbox.isChecked():
                self.save_remembered_username(username)
            else:
                self.save_remembered_username("")
            
            print(f"[LOGIN] Success for: {username} ({role})")
            self.show_success(f"✅ Đăng nhập thành công!\nXin chào {full_name} ({role})")
            self.login_success.emit(username, role)
            QTimer.singleShot(1000, self.accept)
            
        except Exception as e:
            error_msg = f"❌ Lỗi đăng nhập: {str(e)}"
            print(f"[LOGIN-ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
    
    def show_error(self, message):
        """Hiển thị thông báo lỗi"""
        if self.status_label:
            self.status_label.setVisible(True)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("""
                color: #d32f2f;
                font-weight: bold;
                background-color: #ffebee;
                border: 1px solid #ef5350;
                border-radius: 4px;
                padding: 8px;
            """)
    
    def show_success(self, message):
        """Hiển thị thông báo thành công"""
        if self.status_label:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("""
                color: #388e3c;
                font-weight: bold;
                background-color: #e8f5e9;
                border: 1px solid #66bb6a;
                border-radius: 4px;
                padding: 8px;
            """)
    
    def save_remembered_username(self, username):
        """Lưu username vào file cài đặt"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), ".login_config")
            with open(config_file, "w") as f:
                f.write(username)
        except:
            pass
    
    def load_remembered_username(self):
        """Tải username đã lưu"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), ".login_config")
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    username = f.read().strip()
                    if username and self.username_input:
                        self.username_input.setText(username)
                        self.password_input.setFocus()
                        if self.remember_checkbox:
                            self.remember_checkbox.setChecked(True)
        except:
            pass


if __name__ == "__main__":
    from database import init_db
    
    init_db()
    
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    
    if dialog.exec() == QDialog.Accepted:
        print("[OK] Login successful")
    else:
        print("[CANCEL] Login cancelled")
