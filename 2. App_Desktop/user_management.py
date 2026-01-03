#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Management Module
Quản lý người dùng – chỉ dành cho ADMIN
"""

import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit,
    QComboBox, QHeaderView, QInputDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from core.db_manager import DBManager
from database import hash_password


class UserManagementDialog(QDialog):
    ROLES = ["ADMIN", "STAFF"]
    STATUS_MAP = {1: "Hoạt động", 0: "Vô hiệu"}

    def __init__(self, parent=None, current_user_role="STAFF"):
        super().__init__(parent)

        if current_user_role != "ADMIN":
            QMessageBox.warning(self, "Từ chối truy cập",
                                "Chỉ ADMIN mới có quyền quản lý người dùng.")
            self.reject()
            return

        self.db = DBManager()
        self.setWindowTitle("Quản lý người dùng")
        self.setMinimumSize(820, 500)

        self._setup_ui()
        self._load_users()

    # ==================================================
    # UI
    # ==================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("QUẢN LÝ NGƯỜI DÙNG")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tên đăng nhập", "Họ tên", "Chức vụ", "Trạng thái", "Điện thoại"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        btn_layout.addWidget(self._create_btn("➕ Thêm", self._add_user))
        btn_layout.addWidget(self._create_btn("✏️ Sửa", self._edit_user))
        btn_layout.addWidget(self._create_btn("🗑️ Xóa", self._delete_user))
        btn_layout.addWidget(self._create_btn("🔑 Đặt lại mật khẩu", self._reset_password))
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_btn("Đóng", self.accept))

        layout.addLayout(btn_layout)

    def _create_btn(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    # ==================================================
    # LOAD DATA
    # ==================================================

    def _load_users(self):
        self.table.setRowCount(0)
        users = self.db.get_all_users()

        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            user_id, username, full_name, role, is_active = u

            self.table.setItem(row, 0, QTableWidgetItem(str(user_id)))
            self.table.setItem(row, 1, QTableWidgetItem(username))
            self.table.setItem(row, 2, QTableWidgetItem(full_name or ""))

            role_item = QTableWidgetItem(role)
            if role == "ADMIN":
                role_item.setForeground(QColor("red"))
            self.table.setItem(row, 3, role_item)

            status_item = QTableWidgetItem(self.STATUS_MAP.get(is_active, "???"))
            status_item.setForeground(QColor("green" if is_active else "red"))
            self.table.setItem(row, 4, status_item)

            self.table.setItem(row, 5, QTableWidgetItem(""))  # phone optional

    # ==================================================
    # ACTIONS
    # ==================================================

    def _add_user(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm người dùng")
        layout = QVBoxLayout(dialog)

        username = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        fullname = QLineEdit()
        role = QComboBox()
        role.addItems(self.ROLES)

        layout.addWidget(QLabel("Tên đăng nhập"))
        layout.addWidget(username)
        layout.addWidget(QLabel("Mật khẩu"))
        layout.addWidget(password)
        layout.addWidget(QLabel("Họ tên"))
        layout.addWidget(fullname)
        layout.addWidget(QLabel("Chức vụ"))
        layout.addWidget(role)

        btn = QPushButton("Lưu")
        btn.clicked.connect(lambda: self._save_new_user(
            dialog, username.text(), password.text(),
            fullname.text(), role.currentText()
        ))
        layout.addWidget(btn)

        dialog.exec()

    def _save_new_user(self, dialog, username, password, fullname, role):
        if not username or not password:
            QMessageBox.warning(self, "Thiếu thông tin", "Nhập username và mật khẩu.")
            return

        ok, err = self.db.add_user(
            username=username,
            password=hash_password(password),
            full_name=fullname,
            role=role
        )

        if not ok:
            QMessageBox.critical(self, "Lỗi DB", err)
            return

        dialog.accept()
        self._load_users()

    def _edit_user(self):
        row = self._get_selected_row()
        if row is None:
            return

        user_id = int(self.table.item(row, 0).text())
        user = self.db.get_user_by_id(user_id)

        if not user:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Chỉnh sửa người dùng")
        layout = QVBoxLayout(dialog)

        fullname = QLineEdit(user["full_name"])
        role = QComboBox()
        role.addItems(self.ROLES)
        role.setCurrentText(user["role"])

        layout.addWidget(QLabel("Họ tên"))
        layout.addWidget(fullname)
        layout.addWidget(QLabel("Chức vụ"))
        layout.addWidget(role)

        btn = QPushButton("Lưu")
        btn.clicked.connect(lambda: self._save_edit_user(
            dialog, user_id, fullname.text(), role.currentText()
        ))
        layout.addWidget(btn)

        dialog.exec()

    def _save_edit_user(self, dialog, user_id, fullname, role):
        ok, err = self.db.update_user(user_id, fullname, role)
        if not ok:
            QMessageBox.critical(self, "Lỗi DB", err)
            return

        dialog.accept()
        self._load_users()

    def _delete_user(self):
        row = self._get_selected_row()
        if row is None:
            return

        user_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text()

        if QMessageBox.question(
            self, "Xác nhận",
            f"Xóa người dùng {username}?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:

            ok, err = self.db.delete_user(user_id)
            if not ok:
                QMessageBox.critical(self, "Lỗi DB", err)
                return

            self._load_users()

    def _reset_password(self):
        row = self._get_selected_row()
        if row is None:
            return

        user_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text()

        pwd, ok = QInputDialog.getText(
            self, "Đặt lại mật khẩu",
            f"Mật khẩu mới cho {username}",
            QLineEdit.Password
        )

        if ok and pwd:
            self.db.reset_password(user_id, hash_password(pwd))
            QMessageBox.information(self, "OK", "Đã cập nhật mật khẩu.")

    # ==================================================
    # UTILS
    # ==================================================

    def _get_selected_row(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn người dùng.")
            return None
        return indexes[0].row()
