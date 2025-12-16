#!/usr/bin/env python3
"""
Debug script to find all widgets in a page
"""
import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from config import PAGES_PATH

def find_all_widgets(widget, indent=0):
    """Recursively print all widgets in a tree"""
    name = widget.objectName() if hasattr(widget, 'objectName') else 'Unknown'
    widget_class = widget.__class__.__name__
    print("  " * indent + f"{widget_class}: {name}")
    
    if hasattr(widget, 'findChildren'):
        children = widget.findChildren(QWidget)
        for child in children:
            if child.parent() == widget:  # Only direct children
                find_all_widgets(child, indent + 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load history.ui
    loader = QUiLoader()
    ui_path = os.path.join(PAGES_PATH, "history.ui")
    
    file = QFile(ui_path)
    if file.open(QFile.ReadOnly):
        widget = loader.load(file)
        file.close()
        
        print("=" * 80)
        print("WIDGETS IN HISTORY PAGE:")
        print("=" * 80)
        find_all_widgets(widget)
        
        print("\n" + "=" * 80)
        print("LOOKING FOR PAGINATION BUTTONS:")
        print("=" * 80)
        
        btn_prev = widget.findChild(QWidget, "btnPrevPage")
        btn_next = widget.findChild(QWidget, "btnNextPage")
        table = widget.findChild(QWidget, "historyTable")
        
        print(f"btnPrevPage: {btn_prev}")
        print(f"btnNextPage: {btn_next}")
        print(f"historyTable: {table}")
        
    else:
        print(f"Cannot open file: {ui_path}")
