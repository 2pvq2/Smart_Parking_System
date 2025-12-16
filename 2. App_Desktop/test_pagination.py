#!/usr/bin/env python3
"""
Test pagination buttons in PySide6
"""
import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class TestPagination(QWidget):
    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.total_pages = 5
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Info label
        self.info_label = QLabel(f"Page {self.current_page + 1}/{self.total_pages}")
        layout.addWidget(self.info_label)
        
        # Prev button
        self.btn_prev = QPushButton("Prev")
        self.btn_prev.clicked.connect(self.prev_page)
        layout.addWidget(self.btn_prev)
        
        # Next button
        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self.next_page)
        layout.addWidget(self.btn_next)
        
        self.setLayout(layout)
        self.setWindowTitle("Test Pagination")
        self.update_buttons()
        
    def prev_page(self):
        print(f"Prev clicked! Current page: {self.current_page}")
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            
    def next_page(self):
        print(f"Next clicked! Current page: {self.current_page}")
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            
    def update_buttons(self):
        self.info_label.setText(f"Page {self.current_page + 1}/{self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)
        print(f"Page {self.current_page + 1}, Prev enabled: {self.current_page > 0}, Next enabled: {self.current_page < self.total_pages - 1}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test = TestPagination()
    test.show()
    test.resize(300, 200)
    sys.exit(app.exec())
