"""Preview loader for app_mainwindow.ui using PySide6.

Usage (PowerShell):
    python ./preview_loader.py

This loads `app_mainwindow.ui` (created in the same folder) and shows the window.
"""
import sys
import os
import urllib.request
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QPushButton, QWidget, QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QLineEdit, QSpinBox, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
import traceback
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def load_ui(path):
    loader = QUiLoader()
    ui_file = QFile(path)
    print(f"Loading UI: {path}")
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Cannot open UI file: {path}")
    widget = loader.load(ui_file)
    ui_file.close()
    return widget


def apply_theme(app_obj: QApplication, theme: str):
    """Load a theme qss: 'light' or 'dark'."""
    base = os.path.dirname(os.path.abspath(__file__))
    qss_file = os.path.join(base, f"styles_{theme}.qss")
    if os.path.exists(qss_file):
        try:
            with open(qss_file, 'r', encoding='utf-8') as f:
                app_obj.setStyleSheet(f.read())
            print(f"Applied theme: {theme}")
        except Exception:
            print(f"Failed to apply theme {theme}")
    else:
        print(f"Theme file not found: {qss_file}")


def set_image_from_url(label: QLabel, url: str):
    try:
        data = urllib.request.urlopen(url, timeout=5).read()
        pix = QPixmap()
        pix.loadFromData(data)
        # scale to label size
        w = label.width() or 320
        h = label.height() or 180
        # avoid zero-dimension scaling
        if w <= 0: w = 320
        if h <= 0: h = 180
        scaled = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled)
    except Exception:
        # fallback: keep text placeholder
        label.setText("Camera feed")


def safe_init_page(widget: QWidget):
    """Attempt to initialize dynamic parts of a page and catch/log any exception so page switching won't crash the preview."""
    if widget is None:
        return
    try:
        # Example: if this is dashboard, ensure images/progress values are populated
        if widget.objectName() in ('DashboardPage', 'dashboard', 'pageDashboard'):
            cam_entry = widget.findChild(QLabel, 'camEntryImage')
            cam_exit = widget.findChild(QLabel, 'camExitImage')
            if cam_entry:
                set_image_from_url(cam_entry, 'https://images.unsplash.com/photo-1653750366046-289780bd8125?auto=format&fit=crop&w=1080&q=80')
            if cam_exit:
                set_image_from_url(cam_exit, 'https://images.unsplash.com/photo-1761707054382-6956707c3747?auto=format&fit=crop&w=1080&q=80')
        # If the page contains tables, ensure headers exist
        tbl = widget.findChild(QTableWidget, 'searchResultsTable')
        if tbl:
            headers = ['Biển số','Ngày vào','Giờ vào','Ngày ra','Giờ ra','Loại xe','Loại vé','Mã thẻ','Phí','Trạng thái']
            tbl.setColumnCount(len(headers))
            tbl.setHorizontalHeaderLabels(headers)
        ht = widget.findChild(QTableWidget, 'historyTable')
        if ht:
            headers = ['STT','Biển số','Ngày gửi','Giờ gửi','Ngày ra','Giờ ra','Loại xe','Loại vé','Thời gian gửi','Giá']
            ht.setColumnCount(len(headers))
            ht.setHorizontalHeaderLabels(headers)
        mt = widget.findChild(QTableWidget, 'monthlyTable')
        if mt:
            headers = ['Biển số','Chủ xe','Mã số thẻ','Loại xe','Đăng ký','Hết hạn','Giá','Trạng thái','Thao tác']
            mt.setColumnCount(len(headers))
            mt.setHorizontalHeaderLabels(headers)
    except Exception:
        print(f"Exception while initializing page '{widget.objectName()}':")
        traceback.print_exc()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    base = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(base, "app_mainwindow.ui")
    # Load global QSS style if present
    # Prefer explicit light/dark theme files. Apply light by default.
    apply_theme(app, 'light')

    # Build main window programmatically (we're no longer using app_mainwindow.ui)
    main_win = QMainWindow()
    main_win.setWindowTitle('J97 Packing - Parking Manager')
    central = QWidget()
    main_win.setCentralWidget(central)
    central_layout = QHBoxLayout(central)
    central_layout.setContentsMargins(8, 8, 8, 8)

    # Left: sidebar (load ui_pages/sidebar.ui if exists)
    sidebar_widget = None
    sidebar_ui_path = os.path.join(base, 'ui_pages', 'sidebar.ui')
    if os.path.exists(sidebar_ui_path):
        try:
            sidebar_widget = load_ui(sidebar_ui_path)
        except Exception:
            sidebar_widget = None

    if sidebar_widget is None:
        # fallback simple sidebar
        sidebar_widget = QWidget()
        sb_layout = QVBoxLayout(sidebar_widget)
        sb_layout.setContentsMargins(8, 8, 8, 8)
        for txt, obj in [('Dashboard', 'btnDashboard'), ('Search', 'btnSearch'), ('Monthly', 'btnMonthly'), ('History', 'btnHistory'), ('Statistics', 'btnStatistics'), ('Settings', 'btnSettings')]:
            b = QPushButton(txt)
            b.setObjectName(obj)
            b.setFlat(True)
            sb_layout.addWidget(b)

    central_layout.addWidget(sidebar_widget)

    # Right: stacked pages area
    stacked = QStackedWidget()
    central_layout.addWidget(stacked, 1)

    window = main_win

    # find main widgets (we have the stacked created above)
    # 'stacked' variable already holds the QStackedWidget

    # Load separate page .ui files from ui_pages folder and add to stacked
    pages = [
        ('dashboard', 'ui_pages/dashboard.ui'),
        ('search', 'ui_pages/search.ui'),
        ('monthly', 'ui_pages/monthly.ui'),
        ('history', 'ui_pages/history.ui'),
        ('statistics', 'ui_pages/statistics.ui'),
        ('settings', 'ui_pages/settings.ui'),
    ]

    loaded_pages = {}
    for name, relpath in pages:
        path = os.path.join(base, relpath)
        if os.path.exists(path):
            try:
                w = load_ui(path)
                stacked.addWidget(w)
                loaded_pages[name] = w
            except Exception:
                print(f"Failed to load page UI: {path}")
                traceback.print_exc()
        else:
            # fallback: use the existing placeholder page if present in main window
            placeholder = None
            loaded_pages[name] = placeholder

    # Sidebar buttons mapping to loaded widgets
    sidebar_btns = [('btnDashboard', 'dashboard'), ('btnSearch', 'search'), ('btnMonthly', 'monthly'), ('btnHistory', 'history'), ('btnStatistics', 'statistics'), ('btnSettings', 'settings')]
    def set_active_button(active_btn: QPushButton):
        for name, _ in sidebar_btns:
            # look for button inside sidebar first, then global window
            b = sidebar_widget.findChild(QPushButton, name) if sidebar_widget is not None else None
            if b is None:
                b = window.findChild(QPushButton, name)
            if not b:
                continue
            is_active = (b is active_btn)
            b.setProperty('active', is_active)
            try:
                b.style().unpolish(b)
                b.style().polish(b)
            except Exception:
                # fallback: force repaint
                b.update()

    for btn_name, page_key in sidebar_btns:
        btn = window.findChild(QPushButton, btn_name)
        page_widget = loaded_pages.get(page_key)
        if btn and page_widget:
            # connect with a safe wrapper so exceptions during initialization are caught
            def make_handler(pw, b):
                def handler(checked=False):
                    try:
                        stacked.setCurrentWidget(pw)
                        safe_init_page(pw)
                        set_active_button(b)
                    except Exception:
                        print(f"Exception while switching to page {pw.objectName()}")
                        traceback.print_exc()
                return handler
            btn.clicked.connect(make_handler(page_widget, btn))

    # Populate dashboard sample data on loaded dashboard page
    dashboard_w = loaded_pages.get('dashboard')
    if dashboard_w:
        # Stats
        for name, text in {'stat1_value': '45', 'stat2_value': '23', 'stat3_value': '156', 'stat4_value': '142'}.items():
            lbl = dashboard_w.findChild(QLabel, name)
            if lbl:
                lbl.setText(text)

        # Availability
        avail1 = dashboard_w.findChild(QProgressBar, 'avail1_progress')
        avail2 = dashboard_w.findChild(QProgressBar, 'avail2_progress')
        if avail1:
            avail1.setValue(54)
        if avail2:
            avail2.setValue(70)

        # Camera images
        cam_entry = dashboard_w.findChild(QLabel, 'camEntryImage')
        cam_exit = dashboard_w.findChild(QLabel, 'camExitImage')
        if cam_entry:
            set_image_from_url(cam_entry, 'https://images.unsplash.com/photo-1653750366046-289780bd8125?auto=format&fit=crop&w=1080&q=80')
        if cam_exit:
            set_image_from_url(cam_exit, 'https://images.unsplash.com/photo-1761707054382-6956707c3747?auto=format&fit=crop&w=1080&q=80')
        # Make sure dashboard is safely initialized for images/headers
        safe_init_page(dashboard_w)

    # Populate history table on loaded history page
    history_w = loaded_pages.get('history')
    if history_w:
        # Sample data copied from your TSX
        sample_history = [
            {'plate': '29A-12345', 'entryDate': '21/11/2024', 'entryTime': '08:30:15', 'exitDate': '21/11/2024', 'exitTime': '17:45:22', 'type': 'Ô tô', 'ticket': 'Vé lượt', 'price': '30.000đ', 'duration': '9h 15m'},
            {'plate': '59H1-23456', 'entryDate': '21/11/2024', 'entryTime': '09:15:30', 'exitDate': '21/11/2024', 'exitTime': '11:30:45', 'type': 'Xe máy', 'ticket': 'Vé lượt', 'price': '5.000đ', 'duration': '2h 15m'},
            {'plate': '30F-67890', 'entryDate': '21/11/2024', 'entryTime': '10:20:45', 'exitDate': '21/11/2024', 'exitTime': '14:10:15', 'type': 'Ô tô', 'ticket': 'Vé lượt', 'price': '20.000đ', 'duration': '3h 50m'},
            {'plate': '51G-98765', 'entryDate': '21/11/2024', 'entryTime': '07:45:00', 'exitDate': '21/11/2024', 'exitTime': '18:20:30', 'type': 'Xe máy', 'ticket': 'Vé tháng', 'price': '0đ', 'duration': '10h 35m'},
            {'plate': '29B-54321', 'entryDate': '20/11/2024', 'entryTime': '15:30:00', 'exitDate': '21/11/2024', 'exitTime': '08:15:22', 'type': 'Ô tô', 'ticket': 'Vé lượt', 'price': '150.000đ', 'duration': '16h 45m'},
        ]

        table: QTableWidget = history_w.findChild(QTableWidget, 'historyTable')
        lblResults = history_w.findChild(QLabel, 'lblResults')
        paginationLabel = history_w.findChild(QLabel, 'paginationLabel')
        btnPrev = history_w.findChild(QPushButton, 'btnPrevPage')
        btnNext = history_w.findChild(QPushButton, 'btnNextPage')
        btnPage1 = history_w.findChild(QPushButton, 'btnPage1')

        if table:
            table.setRowCount(len(sample_history))
            table.setColumnCount(10)
            for i, rec in enumerate(sample_history):
                items = [
                    str(i+1),
                    rec['plate'],
                    rec['entryDate'],
                    rec['entryTime'],
                    rec['exitDate'],
                    rec['exitTime'],
                    rec['type'],
                    rec['ticket'],
                    rec['duration'],
                    rec['price'],
                ]
                for j, val in enumerate(items):
                    table.setItem(i, j, QTableWidgetItem(val))

        # Update labels / pagination
        total = len(sample_history)
        if lblResults:
            lblResults.setText(f"Danh sách lịch sử ({total} kết quả)")
        if paginationLabel:
            paginationLabel.setText(f"Hiển thị 1-{total} của {total} kết quả")
        if btnPrev:
            btnPrev.setDisabled(True)
        if btnNext:
            btnNext.setDisabled(True)
        if btnPage1:
            btnPage1.setDisabled(False)

    # Populate monthly tickets table on loaded monthly page
    monthly_w = loaded_pages.get('monthly')
    if monthly_w:
        sample_monthly = [
            {'plate': '29A-12345', 'owner': 'Nguyễn Văn A', 'cardNumber': 'VIP-001234', 'type': 'Ô tô', 'registrationDate': '01/11/2024', 'expiryDate': '01/12/2024', 'price': '1.500.000đ', 'status': 'Còn hạn'},
            {'plate': '59H1-23456', 'owner': 'Trần Thị B', 'cardNumber': 'VIP-005678', 'type': 'Xe máy', 'registrationDate': '05/11/2024', 'expiryDate': '05/12/2024', 'price': '300.000đ', 'status': 'Còn hạn'},
            {'plate': '30F-67890', 'owner': 'Lê Văn C', 'cardNumber': 'VIP-009012', 'type': 'Ô tô', 'registrationDate': '10/10/2024', 'expiryDate': '10/11/2024', 'price': '1.500.000đ', 'status': 'Hết hạn'},
        ]

        table: QTableWidget = monthly_w.findChild(QTableWidget, 'monthlyTable')
        search = monthly_w.findChild(QWidget, 'monthlySearch')
        if table:
            table.setRowCount(len(sample_monthly))
            table.setColumnCount(9)
            for i, t in enumerate(sample_monthly):
                vals = [t['plate'], t['owner'], t['cardNumber'], t['type'], t['registrationDate'], t['expiryDate'], t['price'], t['status'], '']
                for j, v in enumerate(vals):
                    table.setItem(i, j, QTableWidgetItem(str(v)))

        # Populate settings page with sample values
        settings_w = loaded_pages.get('settings')
        if settings_w:
            # General
            pn = settings_w.findChild(QLineEdit, 'parkingName')
            addr = settings_w.findChild(QLineEdit, 'address')
            phone = settings_w.findChild(QLineEdit, 'phone')
            email = settings_w.findChild(QLineEdit, 'email')
            timezone = settings_w.findChild(QComboBox, 'timezone')
            if pn:
                pn.setText('Bãi đỗ xe ABC')
            if addr:
                addr.setText('123 Đường ABC, Quận 1, TP.HCM')
            if phone:
                phone.setText('0123 456 789')
            if email:
                email.setText('contact@parking.com')
            if timezone:
                # default to VN (index 0)
                timezone.setCurrentIndex(0)

            # Pricing
            def set_line(name, value):
                w = settings_w.findChild(QLineEdit, name)
                if w:
                    w.setText(value)

            set_line('motor_first', '5000')
            set_line('motor_next', '3000')
            set_line('motor_max', '30000')
            set_line('car_first', '20000')
            set_line('car_next', '10000')
            set_line('car_max', '150000')
            set_line('monthly_motor', '300000')
            set_line('monthly_car', '1500000')

            # Parking counts and devices
            totalCar = settings_w.findChild(QSpinBox, 'totalCar')
            totalMotor = settings_w.findChild(QSpinBox, 'totalMotor')
            camEntry = settings_w.findChild(QCheckBox, 'camEntry')
            camExit = settings_w.findChild(QCheckBox, 'camExit')
            barrierAuto = settings_w.findChild(QCheckBox, 'barrierAuto')
            if totalCar:
                totalCar.setValue(50)
            if totalMotor:
                totalMotor.setValue(150)
            if camEntry:
                camEntry.setChecked(True)
            if camExit:
                camExit.setChecked(True)
            if barrierAuto:
                barrierAuto.setChecked(False)

            # Notification settings
            notifyNearFull = settings_w.findChild(QCheckBox, 'notifyNearFull')
            notifyMonthlyExpiry = settings_w.findChild(QCheckBox, 'notifyMonthlyExpiry')
            notifyCameraError = settings_w.findChild(QCheckBox, 'notifyCameraError')
            notifyDailyReport = settings_w.findChild(QCheckBox, 'notifyDailyReport')
            notifyEmail = settings_w.findChild(QLineEdit, 'notifyEmail')
            if notifyNearFull:
                notifyNearFull.setChecked(True)
            if notifyMonthlyExpiry:
                notifyMonthlyExpiry.setChecked(True)
            if notifyCameraError:
                notifyCameraError.setChecked(True)
            if notifyDailyReport:
                notifyDailyReport.setChecked(False)
            if notifyEmail:
                notifyEmail.setText('admin@parking.com')

        # Wire dark mode checkbox if present
        if settings_w:
            chk = settings_w.findChild(QCheckBox, 'chkDarkMode')
            try:
                # set initial state based on whether dark theme file exists
                dark_path = os.path.join(base, 'styles_dark.qss')
                if os.path.exists(dark_path):
                    chk.setEnabled(True)
                    chk.setChecked(False)
                    # connect toggle
                    chk.toggled.connect(lambda checked: apply_theme(app, 'dark' if checked else 'light'))
                else:
                    if chk:
                        chk.setEnabled(False)
            except Exception:
                pass

        # Populate statistics page: render charts with matplotlib and set into QLabel placeholders
        stats_w = loaded_pages.get('statistics')
        if stats_w:
            # Sample data from TSX
            revenueData = [
                {'month': 'T1', 'revenue': 45000000, 'cars': 1200, 'motorbikes': 3400},
                {'month': 'T2', 'revenue': 42000000, 'cars': 1150, 'motorbikes': 3200},
                {'month': 'T3', 'revenue': 48000000, 'cars': 1300, 'motorbikes': 3600},
                {'month': 'T4', 'revenue': 52000000, 'cars': 1400, 'motorbikes': 3800},
                {'month': 'T5', 'revenue': 55000000, 'cars': 1500, 'motorbikes': 4000},
                {'month': 'T6', 'revenue': 58000000, 'cars': 1600, 'motorbikes': 4200},
            ]
            vehicleTypeData = [
                {'name': 'Ô tô', 'value': 45, 'color': '#3b82f6'},
                {'name': 'Xe máy', 'value': 55, 'color': '#10b981'},
            ]
            ticketTypeData = [
                {'name': 'Vé lượt', 'value': 65, 'color': '#f59e0b'},
                {'name': 'Vé tháng', 'value': 35, 'color': '#8b5cf6'},
            ]
            hourlyData = [
                {'hour': '00-03', 'count': 12},
                {'hour': '03-06', 'count': 8},
                {'hour': '06-09', 'count': 145},
                {'hour': '09-12', 'count': 98},
                {'hour': '12-15', 'count': 76},
                {'hour': '15-18', 'count': 156},
                {'hour': '18-21', 'count': 134},
                {'hour': '21-24', 'count': 45},
            ]

            def fig_to_pixmap(fig):
                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight')
                plt.close(fig)
                buf.seek(0)
                data = buf.read()
                pix = QPixmap()
                pix.loadFromData(data)
                return pix

            # Revenue bar chart
            months = [d['month'] for d in revenueData]
            revenues = [d['revenue'] for d in revenueData]
            fig, ax = plt.subplots(figsize=(6, 3))
            bars = ax.bar(months, [r/1e6 for r in revenues], color='#3b82f6')
            ax.set_ylabel('Triệu đồng')
            ax.set_title('Doanh thu (triệu đồng)')
            for bar, val in zip(bars, revenues):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{int(val/1e6)}", ha='center', va='bottom')
            revenue_pix = fig_to_pixmap(fig)
            lbl = stats_w.findChild(QLabel, 'revenueChart')
            if lbl:
                lbl.setPixmap(revenue_pix.scaled(lbl.width() or 400, lbl.height() or 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Vehicle count line chart
            cars = [d['cars'] for d in revenueData]
            motors = [d['motorbikes'] for d in revenueData]
            fig, ax = plt.subplots(figsize=(6,3))
            ax.plot(months, cars, marker='o', color='#3b82f6', label='Ô tô')
            ax.plot(months, motors, marker='o', color='#10b981', label='Xe máy')
            ax.set_title('Lượng xe theo tháng')
            ax.legend()
            vehicle_pix = fig_to_pixmap(fig)
            lbl2 = stats_w.findChild(QLabel, 'vehicleCountChart')
            if lbl2:
                lbl2.setPixmap(vehicle_pix.scaled(lbl2.width() or 400, lbl2.height() or 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Pie charts
            def make_pie(data):
                labels = [d['name'] for d in data]
                sizes = [d['value'] for d in data]
                colors = [d['color'] for d in data]
                fig, ax = plt.subplots(figsize=(4,3))
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
                ax.axis('equal')
                return fig

            fig = make_pie(vehicleTypeData)
            pix = fig_to_pixmap(fig)
            pv = stats_w.findChild(QLabel, 'pieVehicleChart')
            if pv:
                pv.setPixmap(pix.scaled(pv.width() or 400, pv.height() or 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            fig = make_pie(ticketTypeData)
            pix = fig_to_pixmap(fig)
            pt = stats_w.findChild(QLabel, 'pieTicketChart')
            if pt:
                pt.setPixmap(pix.scaled(pt.width() or 400, pt.height() or 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Hourly bar chart
            hrs = [d['hour'] for d in hourlyData]
            counts = [d['count'] for d in hourlyData]
            fig, ax = plt.subplots(figsize=(10,3))
            ax.bar(hrs, counts, color='#f59e0b')
            ax.set_title('Lượng xe theo giờ')
            hourly_pix = fig_to_pixmap(fig)
            hl = stats_w.findChild(QLabel, 'hourlyChart')
            if hl:
                hl.setPixmap(hourly_pix.scaled(hl.width() or 820, hl.height() or 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    # Populate search results on loaded search page
    search_w = loaded_pages.get('search')
    if search_w:
        sample_search = [
            {'plate': '29A-12345', 'entryDate': '21/11/2024', 'entryTime': '08:30:15', 'exitDate': '21/11/2024', 'exitTime': '17:45:22', 'type': 'Ô tô', 'ticket': 'Vé lượt', 'cardNumber': 'PKL-001234', 'fee': '30.000đ', 'status': 'Đã ra'},
            {'plate': '59H1-23456', 'entryDate': '21/11/2024', 'entryTime': '09:15:30', 'exitDate': '-', 'exitTime': '-', 'type': 'Xe máy', 'ticket': 'Vé tháng', 'cardNumber': 'PKL-005678', 'fee': '-', 'status': 'Đang gửi'},
            {'plate': '30F-67890', 'entryDate': '21/11/2024', 'entryTime': '10:20:45', 'exitDate': '-', 'exitTime': '-', 'type': 'Ô tô', 'ticket': 'Vé lượt', 'cardNumber': 'PKL-009012', 'fee': '-', 'status': 'Đang gửi'},
        ]

        table: QTableWidget = search_w.findChild(QTableWidget, 'searchResultsTable')
        if table:
            table.setRowCount(len(sample_search))
            table.setColumnCount(10)
            for i, rec in enumerate(sample_search):
                vals = [rec['plate'], rec['entryDate'], rec['entryTime'], rec['exitDate'], rec['exitTime'], rec['type'], rec['ticket'], rec['cardNumber'], rec['fee'], rec['status']]
                for j, v in enumerate(vals):
                    table.setItem(i, j, QTableWidgetItem(str(v)))

    # Show window
    window.show()
    # If AUTO_SWITCH env var is set, cycle pages programmatically to reproduce switch-related issues
    if os.environ.get('AUTO_SWITCH'):
        def cycle_pages():
            try:
                count = stacked.count()
                # cycle through pages forward and back
                for i in range(count):
                    stacked.setCurrentIndex(i)
                    safe_init_page(stacked.currentWidget())
                for i in reversed(range(count)):
                    stacked.setCurrentIndex(i)
                    safe_init_page(stacked.currentWidget())
                print('Auto-switch cycle complete')
            except Exception:
                print('Exception during auto-switch:')
                traceback.print_exc()

        # run after 500ms to allow window to initialize
        QTimer.singleShot(500, cycle_pages)

    sys.exit(app.exec())

