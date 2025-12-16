#!/usr/bin/env python3
"""
Test script to verify history table header display
"""
import sys
import os

# Add the main app directory to path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

# Create a test app
app = QApplication(sys.argv)

# Create a test table
table = QTableWidget()
table.setColumnCount(14)
table.setRowCount(2)

# Set headers
headers = ["ID", "Mã thẻ", "Biển số", "Loại xe", "Ô đỗ", 
           "Giờ vào", "Giờ ra", "Thời gian đỗ", "Loại vé", "Chủ xe",
           "Phí", "Thanh toán", "Trạng thái", "Ảnh vào"]
table.setHorizontalHeaderLabels(headers)

# Make headers visible
table.horizontalHeader().setVisible(True)
table.verticalHeader().setVisible(True)
table.horizontalHeader().setMinimumHeight(30)

# Add test data
for row in range(2):
    for col in range(14):
        item = QTableWidgetItem(f"Row{row}-Col{col}")
        table.setItem(row, col, item)

# Display
table.setWindowTitle("Test History Table")
table.resize(1200, 300)
table.show()

print("✅ Test table created and displayed")
print(f"Header visible: {table.horizontalHeader().isVisible()}")
print(f"Header height: {table.horizontalHeader().height()}")
print(f"Number of columns: {table.columnCount()}")

# Run app
sys.exit(app.exec())
