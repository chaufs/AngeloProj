from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
                             QLineEdit, QComboBox, QSpinBox, QCalendarWidget, QTableWidget, QStackedWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QDateEdit,
                             QScrollArea, QDialog, QTableView, QStyleFactory, QTabWidget, QCheckBox,
                             QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QPixmap
from datetime import datetime
import os

# --- STYLES ---
INPUT_STYLE = "padding: 10px; border: 1px solid #BDC3C7; border-radius: 5px; font-size: 14px; background: white; color: black;"
BTN_STYLE = "QPushButton { background-color: #2C3E50; color: white; font-weight: bold; border-radius: 5px; padding: 12px; } QPushButton:hover { background-color: #34495E; }"
SIDEBAR_BG = "background-color: #1A1A1D; color: white;"
CARD_STYLE = """
    QFrame { 
        background-color: white; 
        border: 1px solid #E0E0E0; 
        border-radius: 10px; 
    } 
    QFrame:hover { 
        border: 2px solid #3498DB; 
    }
"""
CALENDAR_STYLE = """
    QCalendarWidget QWidget { alternate-background-color: #F7F9F9; background-color: white; }
    QCalendarWidget QWidget#qt_calendar_navigationbar { background-color: #2C3E50; border: none; }
    QCalendarWidget QSpinBox { background-color: transparent; color: white; font-weight: bold; }
    QCalendarWidget QToolButton { color: white; font-weight: bold; icon-size: 24px; background-color: transparent; }
    QCalendarWidget QAbstractItemView { font-size: 14px; selection-background-color: #3498DB; selection-color: white; }
"""
SPINBOX_STYLE = """
    QSpinBox { padding: 5px 10px; border: 2px solid #BDC3C7; border-radius: 5px; font-size: 14px; background: white; color: #2C3E50; font-weight: bold; }
    QSpinBox:focus { border: 2px solid #3498DB; }
"""


class StaffWindow(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl

        self.setStyleSheet("""
            QWidget { background-color: white; color: #2C3E50; font-family: 'Segoe UI', sans-serif; }
            QFrame#Sidebar { background-color: #1A1A1D; }
            QLabel { color: #2C3E50; }
            QLineEdit, QComboBox, QSpinBox { color: black; }
        """)

        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(SIDEBAR_BG)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo Area
        logo_box = QFrame()
        logo_box.setFixedHeight(80)
        logo_box.setStyleSheet("background-color: #B71C1C;")
        lbl_logo = QLabel("HOTELLA\nSTAFF", logo_box)
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("color: #F4D03F; font-size: 22px; font-weight: 900; background: transparent;")
        vl = QVBoxLayout(logo_box)
        vl.addWidget(lbl_logo)
        sb_layout.addWidget(logo_box)
        sb_layout.addSpacing(20)

        self.stack = QStackedWidget()
        self.btns = []

        # Initialize Dashboard
        self.dashboard_page = DashboardPage(ctrl)
        self.dashboard_page.navigate_signal.connect(self.nav)

        # Page List
        # 0=Dash, 1=All, 2=Book, 3=Svc, 4=Pay, 5=House
        self.stack.addWidget(self.dashboard_page)  # Index 0
        self.stack.addWidget(BookingsManagerPage(ctrl))  # Index 1
        self.stack.addWidget(BookingPage(ctrl))  # Index 2
        self.stack.addWidget(ServicesPage(ctrl))  # Index 3
        self.stack.addWidget(PaymentPage(ctrl))  # Index 4
        self.stack.addWidget(HousekeepingPage(ctrl))  # Index 5

        page_names = ["DASHBOARD", "ALL BOOKINGS", "BOOK A ROOM", "SERVICES", "PAYMENT", "HOUSEKEEPING"]

        for i, name in enumerate(page_names):
            btn = QPushButton(name)
            btn.setFixedHeight(55)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding-left: 30px; color: #ECF0F1; border: none; font-weight: 600; font-size: 14px; background: transparent; } 
                QPushButton:checked { background-color: #F4D03F; color: black; border-left: 5px solid #B71C1C; }
                QPushButton:hover { background-color: #34495E; }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self.nav(idx))
            sb_layout.addWidget(btn)
            self.btns.append(btn)

        sb_layout.addStretch()

        # Logout button logic
        btn_logout = QPushButton("LOG OUT")
        btn_logout.setFixedHeight(55)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(
            "QPushButton { color: white; font-weight: bold; border: none; font-size: 14px; } QPushButton:hover { color:gray }")
        btn_logout.clicked.connect(lambda: self.window().close())
        sb_layout.addWidget(btn_logout)

        main.addWidget(sidebar)
        main.addWidget(self.stack)
        self.nav(0)

    def nav(self, idx):
        # Update Sidebar Buttons
        for b in self.btns: b.setChecked(False)
        self.btns[idx].setChecked(True)

        # Switch Page
        self.stack.setCurrentIndex(idx)

        # Auto-refresh if the page supports it
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()


class ClickableCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, color, value, title, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: {color}; 
                border-radius: 10px; 
                color: white; 
            }}
            QFrame:hover {{
                border: 2px solid white;
            }}
        """)
        self.setFixedHeight(120)

        vbox = QVBoxLayout(self)
        lbl_val = QLabel(str(value))
        lbl_val.setStyleSheet("font-size: 40px; font-weight: 800; color: white; background: transparent; border: none;")

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; color: white; background: transparent; border: none;")

        vbox.addWidget(lbl_val)
        vbox.addWidget(lbl_title)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# --- PAGE 0: DASHBOARD (UPDATED LAYOUT) ---
class DashboardPage(QWidget):
    # Signal to tell the main window to change tabs
    navigate_signal = pyqtSignal(int)

    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(30, 30, 30, 30)  # Adjusted margins to match Admin
        l.setSpacing(20)

        # 🟢 NEW: Stylish Header (Matches Admin Layout)
        header_frame = QFrame()
        header_frame.setFixedHeight(100)
        # Red Gradient to match Staff Theme (Dark Red to Red Orange)
        header_frame.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C0392B, stop:1 #E74C3C); border-radius: 15px;")

        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(25, 0, 25, 0)

        lbl_title = QLabel("Staff Dashboard")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 800; color: white; background: transparent;")
        h_layout.addWidget(lbl_title)

        h_layout.addStretch()

        # Time and Date Labels
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet("font-size: 24px; color: white; background: transparent; font-weight: bold;")
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet("font-size: 14px; color: white; background: transparent;")

        right_vbox = QVBoxLayout()
        right_vbox.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_vbox.addWidget(self.time_lbl)
        right_vbox.addWidget(self.date_lbl)

        h_layout.addLayout(right_vbox)
        l.addWidget(header_frame)

        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        l.addLayout(self.grid)
        l.addStretch()

        timer = QTimer(self)
        timer.timeout.connect(self.upd)
        timer.start(1000)
        self.upd()

    def upd(self):
        # Update clock with 12-hour format
        self.time_lbl.setText(datetime.now().strftime('%I:%M:%S %p'))
        self.date_lbl.setText(datetime.now().strftime('%A, %B %d, %Y'))

    def refresh(self):
        # 1. Clear existing items safely
        if self.grid is not None:
            while self.grid.count():
                item = self.grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # 2. Get Stats safely
        try:
            total, vac, occ, dirt = self.ctrl.get_stats()
            # Check for Overstayers
            if hasattr(self.ctrl, 'get_overdue_guests'):
                overstayers = self.ctrl.get_overdue_guests()
            else:
                overstayers = []
        except Exception as e:
            print(f"Stats Error: {e}")
            total, vac, occ, dirt = 0, 0, 0, 0
            overstayers = []

        # 3. Check for Overstayers (Alert Box)
        row_offset = 0
        if overstayers:
            alert_frame = QFrame()
            alert_frame.setStyleSheet("background-color: #C0392B; border-radius: 10px; color: white;")
            alert_frame.setFixedHeight(120)
            al = QVBoxLayout(alert_frame)

            header = QLabel(f"⚠️ {len(overstayers)} GUEST(S) OVERSTAYING")
            header.setStyleSheet("font-weight:bold; font-size:16px; border:none; color:white; background:transparent;")
            al.addWidget(header)

            txt = "\n".join([f"• Room {g.get('room', '?')} ({g.get('name', 'Guest')})" for g in overstayers])
            details = QLabel(txt)
            details.setStyleSheet("border:none; color:white; background:transparent;")
            al.addWidget(details)

            self.grid.addWidget(alert_frame, 0, 0, 1, 2)
            row_offset = 1

        # 4. Define Cards
        # Indices: 1=All Bookings, 2=Book Room, 3=Services, 5=Housekeeping
        cards_data = [
            ("TOTAL BOOKINGS", total, "#3498DB", 1),
            ("VACANT ROOMS", vac, "#27AE60", 2),
            ("OCCUPIED", occ, "#E74C3C", 3),
            ("HOUSEKEEPING", dirt, "#F39C12", 5)
        ]

        for i, (title, val, color, target_idx) in enumerate(cards_data):
            card = ClickableCard(color, val, title)
            # Use default argument capture to fix lambda scoping
            card.clicked.connect(lambda checked=False, idx=target_idx: self.navigate_signal.emit(idx))
            self.grid.addWidget(card, (i // 2) + row_offset, i % 2)


# --- PAGE 1: ALL BOOKINGS ---
class BookingsManagerPage(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("Booking Management",
                                styleSheet="font-size: 24px; font-weight: 800; color: #2C3E50; margin-bottom: 10px;"))

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #DDD; background: white; border-radius: 5px; }
            QTabBar::tab { background: #E0E0E0; color: #333; padding: 12px 25px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; font-weight: bold; }
            QTabBar::tab:selected { background: #3498DB; color: white; }
            QTabBar::tab:hover { background: #BDC3C7; }
        """)

        self.tab_today = TodayBookingsTab(ctrl)
        self.tabs.addTab(self.tab_today, "📅 Today's Bookings")

        self.tab_all = AllBookingsTab(ctrl)
        self.tabs.addTab(self.tab_all, "📚 All Bookings History")

        self.tabs.currentChanged.connect(self.on_tab_change)
        layout.addWidget(self.tabs)

    def on_tab_change(self, index):
        if index == 0:
            self.tab_today.refresh()
        else:
            self.tab_all.refresh()

    def refresh(self):
        self.on_tab_change(self.tabs.currentIndex())


class TodayBookingsTab(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        l.addWidget(QLabel("Guests Arriving Today", styleSheet="font-size: 18px; font-weight: bold; color: #2C3E50;"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(content)
        l.addWidget(scroll)

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bookings = self.ctrl.get_todays_arrivals()
        if not bookings:
            self.grid.addWidget(
                QLabel("No arrivals scheduled for today.", styleSheet="color: #7f8c8d; font-size: 14px;"), 0, 0)
            return

        r, c = 0, 0
        for b in bookings:
            self.grid.addWidget(self.create_card(b), r, c)
            c += 1
            if c > 3:
                c = 0
                r += 1

    def create_card(self, b):
        card = QFrame()
        card.setFixedSize(220, 160)
        card.setStyleSheet(CARD_STYLE)
        v = QVBoxLayout(card)

        v.addWidget(QLabel(b['name'], styleSheet="font-weight:bold; font-size:15px; border:none; color:#2C3E50;"))
        v.addWidget(QLabel(f"ID: {b['bid']}", styleSheet="color:#7F8C8D; font-size:12px; border:none;"))
        v.addWidget(
            QLabel(f"Room: {b['room']} ({b['type']})", styleSheet="color:#E67E22; font-weight:bold; border:none;"))

        current_status = str(b.get('status', '')).strip().lower()

        if current_status not in ['arrived', 'checked in']:
            btn_box = QHBoxLayout()
            btn1 = QPushButton("✓ Check-In")
            btn1.setStyleSheet("background:#27AE60; color:white; border-radius:4px; font-weight:bold; border:none;")
            btn2 = QPushButton("✕ Cancel")
            btn2.setStyleSheet("background:#E74C3C; color:white; border-radius:4px; font-weight:bold; border:none;")

            btn1.clicked.connect(lambda: self.do_action(b, "Check-In"))
            btn2.clicked.connect(lambda: self.do_action(b, "Cancelled"))

            btn_box.addWidget(btn1)
            btn_box.addWidget(btn2)
            v.addLayout(btn_box)
        else:
            v.addStretch()
            status_lbl = QLabel("Checked In")
            status_lbl.setStyleSheet("color: #27AE60; font-weight: 800; border: none; font-size: 16px;")
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(status_lbl)

        return card

    def do_action(self, b, action):
        msg = f"Confirm {action} for {b['name']}?"
        if QMessageBox.question(self, "Confirm", msg) == QMessageBox.StandardButton.Yes:
            if action == "Check-In":
                success, res_msg = self.ctrl.mark_arrived(b['bid'], b['name'])
                if success:
                    QMessageBox.information(self, "Success", res_msg)
                else:
                    QMessageBox.warning(self, "Check-In Blocked", res_msg)
            else:
                self.ctrl.cancel_booking_today(b['bid'], b['name'])

            self.refresh()


class AllBookingsTab(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        top = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Search Guest or ID...")
        self.search.setStyleSheet(INPUT_STYLE)
        self.search.textChanged.connect(self.refresh)
        self.cb_filter = QComboBox()
        self.cb_filter.addItems(["All", "Confirmed", "Cancelled", "Checked Out"])
        self.cb_filter.setStyleSheet(INPUT_STYLE)
        self.cb_filter.currentTextChanged.connect(self.refresh)
        top.addWidget(QLabel("Search:"))
        top.addWidget(self.search)
        top.addWidget(QLabel("Filter:"))
        top.addWidget(self.cb_filter)
        l.addLayout(top)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(content)
        l.addWidget(scroll)

    def refresh(self):
        while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
        all_b = self.ctrl.get_all_bookings()
        txt = self.search.text().lower()
        stat = self.cb_filter.currentText()
        filtered = [b for b in all_b if
                    (txt in b['name'].lower() or txt in b['bid'].lower()) and (stat == "All" or b['status'] == stat)]
        r, c = 0, 0
        for b in filtered:
            self.grid.addWidget(self.create_card(b), r, c)
            c += 1
            if c > 3: c = 0; r += 1

    def create_card(self, b):
        card = QFrame()
        card.setFixedSize(220, 150)
        bg = "#ECF0F1" if b['status'] != 'Confirmed' else "white"
        br = "#BDC3C7" if b['status'] != 'Confirmed' else "#3498DB"
        card.setStyleSheet(f"QFrame {{ background: {bg}; border: 2px solid {br}; border-radius: 8px; }}")
        v = QVBoxLayout(card)
        v.addWidget(QLabel(b['bid'], styleSheet="font-weight:bold; color:#2C3E50; border:none;"))
        v.addWidget(QLabel(b['name'], styleSheet="font-size:14px; border:none;"))
        v.addWidget(QLabel(f"{b['date']} ({b['days']} days)", styleSheet="color:#7F8C8D; font-size:12px; border:none;"))
        v.addWidget(QLabel(b['status'],
                           styleSheet=f"color:{'red' if b['status'] == 'Cancelled' else 'green'}; font-weight:bold; border:none;"))
        return card


# --- PAGE 2: BOOK A ROOM ---
class BookingPage(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.selected_room = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #E0E0E0;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(25, 25, 25, 25)
        lp_layout.setSpacing(15)

        lp_layout.addWidget(
            QLabel("Guest Details", styleSheet="font-size: 20px; font-weight: 800; color: #2C3E50;border:0px;"))
        self.inp = {}
        for f in ["Name", "Email", "Phone", "Address"]:
            lp_layout.addWidget(QLabel(f, styleSheet="font-weight:bold; color:#555;border:0px;"))
            t = QLineEdit(placeholderText=f"Enter {f}")
            t.setStyleSheet(INPUT_STYLE)
            lp_layout.addWidget(t)
            self.inp[f] = t

        lp_layout.addWidget(QLabel("Number of Guests", styleSheet="font-weight:bold; color:#555;border:0px;"))
        self.spin_guests = QSpinBox()
        self.spin_guests.setRange(1, 10)
        self.spin_guests.setStyleSheet(SPINBOX_STYLE)
        lp_layout.addWidget(self.spin_guests)

        self.lbl_sel = QLabel("No Room Selected", styleSheet="color: #E74C3C; font-weight: bold;border:0px;")
        self.lbl_tot = QLabel("Total: ₱0", styleSheet="font-size: 22px; font-weight: 900; color: #27AE60;border:0px")
        lp_layout.addWidget(self.lbl_sel)
        lp_layout.addWidget(self.lbl_tot)
        lp_layout.addStretch()

        btn_pay = QPushButton("PROCEED TO PAYMENT")
        btn_pay.setStyleSheet(BTN_STYLE)
        btn_pay.clicked.connect(self.pay)
        lp_layout.addWidget(btn_pay)

        layout.addWidget(left_panel)

        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)

        ctrl_section = QFrame()
        ctrl_section.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #E0E0E0;")
        cs_layout = QHBoxLayout(ctrl_section)

        self.cal = QCalendarWidget()
        self.cal.setFixedHeight(250)
        self.cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.cal.setStyleSheet(CALENDAR_STYLE)
        self.cal.clicked.connect(self.load_rooms)

        dur_box = QVBoxLayout()
        dur_box.addWidget(QLabel("Booking Duration:", styleSheet="font-weight:bold;border:0px;"))

        self.dur = QSpinBox()
        self.dur.setRange(1, 30)
        self.dur.setSuffix(" Night(s)")
        self.dur.setFixedHeight(40)
        self.dur.setStyleSheet(SPINBOX_STYLE)
        self.dur.valueChanged.connect(self.load_rooms)

        btn_refresh = QPushButton("Check Availability")
        btn_refresh.setStyleSheet("background: #3498DB; color: white; padding: 10px;")
        btn_refresh.clicked.connect(self.load_rooms)

        dur_box.addWidget(self.dur)
        dur_box.addWidget(btn_refresh)
        dur_box.addStretch()

        cs_layout.addWidget(self.cal, stretch=2)
        cs_layout.addLayout(dur_box, stretch=1)

        rp_layout.addWidget(ctrl_section)

        rp_layout.addWidget(QLabel("Available Rooms (Select One):", styleSheet="font-weight:bold; margin-top:10px;"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        room_container = QWidget()
        self.grid = QGridLayout(room_container)
        scroll.setWidget(room_container)
        rp_layout.addWidget(scroll)

        layout.addWidget(right_panel)

    def load_rooms(self):
        if self.cal.selectedDate() < QDate.currentDate():
            while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
            self.lbl_sel.setText("Invalid Date Selected")
            return

        while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
        self.selected_room = None
        self.lbl_tot.setText("Total: ₱0")

        d_in = self.cal.selectedDate().toString("yyyy-MM-dd")
        d_out = self.cal.selectedDate().addDays(self.dur.value()).toString("yyyy-MM-dd")

        rooms = self.ctrl.search_rooms(d_in, d_out)
        prices = self.ctrl.get_room_prices()

        r, c = 0, 0
        for rm in rooms:
            p = prices.get(rm[1], 1500)
            btn = QPushButton(f"Room {rm[0]}\n{rm[1]}\n₱{p}/night")
            btn.setCheckable(True)
            btn.setFixedSize(140, 100)
            btn.setStyleSheet(
                "QPushButton { background: #2ECC71; color: white; border-radius: 8px; font-weight: bold; } QPushButton:checked { background: #27AE60; border: 3px solid #F1C40F; }")
            btn.clicked.connect(lambda ch, x=rm[0], y=rm[1], z=p, b=btn: self.select_room(x, y, z, b))
            self.grid.addWidget(btn, r, c)
            c += 1
            if c > 3: c = 0; r += 1

    def select_room(self, rid, rtype, price, btn):
        for i in range(self.grid.count()):
            w = self.grid.itemAt(i).widget()
            if w != btn: w.setChecked(False)
        btn.setChecked(True)
        self.selected_room = {'id': rid, 'type': rtype, 'price': price}
        total = price * self.dur.value()
        self.lbl_sel.setText(f"Selected: {rid} ({rtype})")
        self.lbl_tot.setText(f"Total: ₱{total:,}")

    def pay(self):
        if self.cal.selectedDate() < QDate.currentDate():
            return QMessageBox.warning(self, "Error", "Cannot book for a past date.")
        if not self.selected_room:
            return QMessageBox.warning(self, "Error", "Please select a room.")
        if not all(v.text().strip() for v in self.inp.values()):
            return QMessageBox.warning(self, "Error", "Please fill in all guest details.")

        total = self.selected_room['price'] * self.dur.value()
        dlg = PaymentDialog(self, total)
        if dlg.exec() == 1:
            b_data = {k: v.text() for k, v in self.inp.items()}
            b_data.update({
                'date': self.cal.selectedDate().toString("yyyy-MM-dd"),
                'days': self.dur.value(),
                'total_price': total,
                'room_type': self.selected_room['type'],
                'guests': self.spin_guests.value()
            })
            res, msg = self.ctrl.create_booking_final(b_data, self.selected_room['id'], dlg.data)
            if res:
                QMessageBox.information(self, "Success", f"Booked Successfully!\nID: {msg}")
                self.load_rooms()
            else:
                QMessageBox.critical(self, "Error", msg)


# ==========================================
# CUSTOM MASKED CARD INPUT WIDGET
# ==========================================
class MaskedCardInput(QLineEdit):
    """Card input that shows masked dots while typing but stores the actual number"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actual_value = ""  # Store the real card number
        self.is_showing = False  # Track if we're showing the real number
        self.setMaxLength(19)  # 16 digits + 3 spaces for formatting

        # Add show/hide button inside the input
        self.toggle_btn = QPushButton("SHOW", self)
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 10px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.1);
                border-radius: 4px;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_visibility)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Position the button
        self.textChanged.connect(self._on_text_changed)

    def resizeEvent(self, event):
        """Position the toggle button on the right side"""
        button_size = self.toggle_btn.size()
        frame_width = self.style().pixelMetric(self.style().PixelMetric.PM_DefaultFrameWidth)
        self.toggle_btn.move(
            self.rect().right() - button_size.width() - frame_width - 5,
            (self.rect().bottom() + 1 - button_size.height()) // 2
        )
        super().resizeEvent(event)

    def _on_text_changed(self, text):
        """Handle text input and masking"""
        if self.is_showing:
            # When showing, update actual_value directly
            self.actual_value = text.replace(' ', '').replace('•', '')
        else:
            # When masked, extract only new digits
            cursor_pos = self.cursorPosition()
            old_len = len(self.actual_value)

            # Remove formatting to get raw input
            raw = text.replace(' ', '').replace('•', '')

            # Only update if it's digits
            if raw.isdigit() or raw == '':
                self.actual_value = raw

                # Update display with masked version
                self.blockSignals(True)
                if len(self.actual_value) > 0:
                    # Format: •••• •••• •••• 1234
                    masked = self._format_card_masked(self.actual_value)
                    self.setText(masked)

                    # Try to maintain cursor position
                    if len(self.actual_value) > old_len:
                        self.setCursorPosition(min(cursor_pos + 1, len(masked)))
                    else:
                        self.setCursorPosition(min(cursor_pos, len(masked)))
                else:
                    self.clear()
                self.blockSignals(False)

    def _format_card_masked(self, number):
        """Format card number with bullets, showing only last 4 digits"""
        if len(number) <= 4:
            return '• ' * len(number)
        else:
            masked_part = '•' * (len(number) - 4)
            visible_part = number[-4:]
            full = masked_part + visible_part

            # Add spaces every 4 characters
            return ' '.join([full[i:i + 4] for i in range(0, len(full), 4)])

    def _format_card_visible(self, number):
        """Format card number with spaces (1234 5678 9012 3456)"""
        return ' '.join([number[i:i + 4] for i in range(0, len(number), 4)])

    def toggle_visibility(self):
        """Toggle between showing and hiding the card number"""
        self.is_showing = not self.is_showing
        self.blockSignals(True)

        if self.is_showing:
            # Show the real number
            self.toggle_btn.setText("SHOW")
            formatted = self._format_card_visible(self.actual_value)
            self.setText(formatted)
        else:
            # Show masked version
            self.toggle_btn.setText("HIDE")
            if self.actual_value:
                masked = self._format_card_masked(self.actual_value)
                self.setText(masked)
            else:
                self.clear()

        self.blockSignals(False)

    def get_card_number(self):
        """Get the actual card number without formatting"""
        return self.actual_value

    def set_card_number(self, number):
        """Set the card number programmatically"""
        self.actual_value = str(number).replace(' ', '')
        if not self.is_showing and self.actual_value:
            self.setText(self._format_card_masked(self.actual_value))
        elif self.actual_value:
            self.setText(self._format_card_visible(self.actual_value))


class PaymentDialog(QDialog):
    def __init__(self, parent, total):
        super().__init__(parent);
        self.setWindowTitle("Payment");
        self.setFixedSize(450, 450)  # Slightly larger for better layout
        self.total = total;
        self.data = {}
        l = QVBoxLayout(self);
        l.setSpacing(15);
        l.setContentsMargins(30, 30, 30, 30)
        l.addWidget(QLabel(f"Total Amount: ₱{total:,}", styleSheet="font-size:20px; font-weight:bold; color:#2C3E50;"))

        # Payment Method Selection
        self.cb = QComboBox();
        self.cb.addItems(["Cash (Walk-in)", "Debit Card", "Credit Card"]);
        self.cb.setStyleSheet(INPUT_STYLE);
        self.cb.currentTextChanged.connect(self.chk);
        l.addWidget(QLabel("Payment Method:"));
        l.addWidget(self.cb)

        # 🟢 NEW: Use MaskedCardInput instead of regular QLineEdit
        self.card_inp = MaskedCardInput(placeholderText="Enter Card Number");
        self.card_inp.setStyleSheet(INPUT_STYLE + " QLineEdit { padding-right: 40px; }");  # Space for toggle button
        self.card_inp.hide();
        l.addWidget(self.card_inp)

        # Amount to pay spinner
        self.spin = QSpinBox();
        self.spin.setRange(0, total);
        self.spin.setValue(int(total * 0.20));
        self.spin.setStyleSheet(INPUT_STYLE)
        self.lbl_amt = QLabel("Amount to Pay:");
        l.addWidget(self.lbl_amt);
        l.addWidget(self.spin)

        self.lbl_note = QLabel("Minimum 20% downpayment required.");
        self.lbl_note.setWordWrap(True);
        self.lbl_note.setStyleSheet("color:#7f8c8d; font-style:italic;");
        l.addWidget(self.lbl_note)

        btn = QPushButton("Confirm Booking");
        btn.setStyleSheet(BTN_STYLE);
        btn.clicked.connect(self.save);
        l.addWidget(btn)
        self.chk("Cash (Walk-in)")

    def chk(self, m):
        # 🟢 UPDATED: Show card input for BOTH Debit and Credit cards
        if "Card" in m:  # This covers both "Debit Card" and "Credit Card"
            self.card_inp.setPlaceholderText(f"Enter {m} Number")
            self.card_inp.show();

            if "Credit" in m:
                # Credit Card: No upfront payment required
                self.spin.hide();
                self.lbl_amt.hide();
                self.spin.setValue(0);
                self.lbl_note.setText("Credit Card Guarantee. No immediate charge.")
            else:
                # Debit Card: Still requires downpayment
                self.spin.show();
                self.lbl_amt.show();
                min_dp = int(self.total * 0.20);
                self.spin.setRange(min_dp, self.total);
                self.spin.setValue(min_dp);
                self.lbl_note.setText(f"Minimum 20% Downpayment: ₱{min_dp:,}")
        else:
            # Cash payment
            self.card_inp.hide();
            self.spin.show();
            self.lbl_amt.show();
            min_dp = int(self.total * 0.20);
            self.spin.setRange(min_dp, self.total);
            self.spin.setValue(min_dp);
            self.lbl_note.setText(f"Minimum 20% Downpayment: ₱{min_dp:,}")

    def save(self):
        method = self.cb.currentText()
        # 🟢 UPDATED: Validate card input for ANY card type
        if "Card" in method:
            card_num = self.card_inp.get_card_number()
            if not card_num or len(card_num) < 12:
                return QMessageBox.warning(self, "Error",
                                           f"Please enter a valid {method} Number (at least 12 digits).")
            self.data = {'amount': self.spin.value(), 'method': method, 'card_number': card_num}
        else:
            self.data = {'amount': self.spin.value(), 'method': method, 'card_number': None}

        self.accept()


# ==========================================
# PAGE 4: SERVICES
# ==========================================
class ServicesPage(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        l.addWidget(QLabel("Guest Services",
                           styleSheet="font-size: 24px; font-weight: 800; color: #2C3E50; margin-bottom: 10px;"))
        l.addWidget(QLabel("Click on a GREEN (Occupied) room to offer services.",
                           styleSheet="color: #7f8c8d; margin-bottom: 20px;"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setSpacing(15)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(content)
        l.addWidget(scroll)
        btn_ref = QPushButton("Refresh Room Status")
        btn_ref.setStyleSheet("background: #2C3E50; color: white; padding: 10px; border-radius: 5px;")
        btn_ref.clicked.connect(self.refresh)
        l.addWidget(btn_ref)
        self.refresh()

    def refresh(self):
        while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
        rooms = self.ctrl.get_map_data()
        r, c = 0, 0
        for rm in rooms:
            self.grid.addWidget(self.create_room_btn(rm), r, c)
            c += 1
            if c > 5: c = 0; r += 1

    def create_room_btn(self, rm):
        room_num, status, desc = rm[0], rm[1], rm[2]
        is_occupied = (status == 'Occupied')
        if is_occupied:
            color = "#2ECC71";
            hover = "#27AE60";
            border = "#27AE60"
        else:
            color = "#95A5A6";
            hover = "#95A5A6";
            border = "#7F8C8D"
        btn = QPushButton(f"{room_num}\n{desc}\n{status}")
        btn.setFixedSize(120, 90)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; border-radius: 8px; font-weight: bold; border: 2px solid {border}; }} QPushButton:hover {{ background-color: {hover}; }}")
        if is_occupied:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.open_service_dialog(room_num))
        else:
            btn.setDisabled(True)
            btn.setStyleSheet(btn.styleSheet() + "QPushButton { opacity: 0.6; }")
        return btn

    def open_service_dialog(self, room_num):
        bid, name = self.ctrl.get_active_room_details(room_num)
        if not bid: return QMessageBox.warning(self, "Error", "Could not find active booking.")
        dlg = ServiceDialog(self, room_num, bid, name, self.ctrl)
        if dlg.exec() == 1: self.refresh()


class ServiceDialog(QDialog):
    def __init__(self, parent, room, bid, name, ctrl):
        super().__init__(parent)
        self.setWindowTitle(f"Services for Room {room}");
        self.setFixedSize(450, 650)
        self.ctrl = ctrl;
        self.bid = bid;
        self.room = room
        l = QVBoxLayout(self);
        l.setSpacing(15);
        l.setContentsMargins(25, 25, 25, 25)
        l.addWidget(QLabel(f"Guest: {name}", styleSheet="font-size: 18px; font-weight: bold; color: #2C3E50;"))
        l.addWidget(QLabel(f"Booking ID: {bid}", styleSheet="color: #7F8C8D;"))
        l.addWidget(QLabel("Select Services to Add:", styleSheet="margin-top: 10px; font-weight: bold;"))
        self.services = [("Breakfast Set", 150), ("Lunch Set", 250), ("Dinner Set", 250), ("Laundry (Per kg)", 100),
                         ("Cleaning Service", 500)]
        self.service_widgets = []
        current_hour = datetime.now().hour
        for svc, price in self.services:
            row = QHBoxLayout()
            cb = QCheckBox(f"{svc} - ₱{price}");
            cb.setStyleSheet("font-size: 14px; padding: 5px;")
            if "Breakfast" in svc and current_hour >= 11: cb.setDisabled(True); cb.setText(f"{svc} - ₱{price} (Ended)")
            spin = QSpinBox();
            spin.setRange(1, 10);
            spin.setEnabled(False);
            spin.setFixedWidth(60)
            cb.toggled.connect(spin.setEnabled);
            row.addWidget(cb);
            row.addWidget(spin);
            l.addLayout(row)
            self.service_widgets.append((cb, spin, svc, price))
        l.addWidget(QLabel("Assigned Staff:", styleSheet="margin-top: 10px; font-weight: bold;"))
        self.cb_emp = QComboBox();
        self.cb_emp.addItems(self.ctrl.get_service_staff_list());
        self.cb_emp.setStyleSheet(INPUT_STYLE);
        l.addWidget(self.cb_emp);
        l.addStretch()
        btn = QPushButton("Add Charges to Bill");
        btn.setStyleSheet(BTN_STYLE);
        btn.clicked.connect(self.save);
        l.addWidget(btn)

    def save(self):
        added = []
        emp = self.cb_emp.currentText()
        if not emp: return QMessageBox.warning(self, "Error", "Please select a staff member.")
        for cb, spin, svc, price in self.service_widgets:
            if cb.isChecked():
                qty = spin.value()
                self.ctrl.add_service_charge(self.bid, self.room, svc, price, qty, emp)
                added.append(f"{svc} (x{qty})")
        if added:
            QMessageBox.information(self, "Success", f"Added services:\n" + "\n".join(added));
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "No services selected.")


# ==========================================
# PAGE 5: CHECKOUT (PAYMENT)
# ==========================================
class PaymentPage(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        l.addWidget(QLabel("Checkout & Payment",
                           styleSheet="font-size: 24px; font-weight: 800; color: #2C3E50; margin-bottom: 10px;"))
        btn_refresh = QPushButton("Refresh List")
        btn_refresh.setStyleSheet(
            "background: #3498DB; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh)
        l.addWidget(btn_refresh)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(20)
        scroll.setWidget(content)
        l.addWidget(scroll)
        self.refresh()

    def refresh(self):
        # 1. Clear existing items safely
        if self.grid is not None:
            while self.grid.count():
                item = self.grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        try:
            data = self.ctrl.get_checkout_cards()
            if not data:
                self.grid.addWidget(
                    QLabel("No occupied rooms pending checkout.", styleSheet="color: #7f8c8d; font-size: 16px;"), 0, 0)
                return

            r, c = 0, 0
            for row_data in data:
                self.grid.addWidget(self.create_card(row_data), r, c)
                c += 1
                if c > 3: c = 0; r += 1
        except Exception as e:
            print(f"Error loading checkout cards: {e}")

    def create_card(self, data):
        # Use ClickableCard class if available, or QFrame with signal
        # We use a standard QFrame here but handle the click carefully
        card = ClickableCard("white", 0, "", self)  # Dummy init
        card.setFixedSize(220, 160)

        # Style based on balance
        if data['final_balance'] > 0:
            status_color = "#E74C3C"
            status_text = f"Due: ₱{data['final_balance']:,}"
            border_color = "#E74C3C"
        else:
            status_color = "#27AE60"
            status_text = "Fully Paid"
            border_color = "#27AE60"

        card.setStyleSheet(
            f"QFrame {{ background-color: white; border: 2px solid {border_color}; border-radius: 10px; }} "
            f"QFrame:hover {{ background-color: #F9F9F9; border: 2px solid #3498DB; }}"
        )

        # Rebuild Layout (ClickableCard default layout needs clearing or ignoring)
        if card.layout():
            QWidget().setLayout(card.layout())  # Detach old layout

        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        layout.addWidget(QLabel(f"Room {data['room']}",
                                styleSheet="font-size: 18px; font-weight: 900; color: #2C3E50; border:none;"))
        lbl_name = QLabel(data['guest'], styleSheet="font-size: 14px; font-weight: bold; color: #555; border:none;")
        lbl_name.setWordWrap(True)
        layout.addWidget(lbl_name)
        layout.addWidget(QLabel(f"ID: {data['bid']}", styleSheet="color: #999; font-size: 12px; border:none;"))
        layout.addStretch()
        layout.addWidget(
            QLabel(status_text, styleSheet=f"font-size: 16px; font-weight: 800; color: {status_color}; border:none;"))

        # Connect Signal
        try:
            card.clicked.disconnect()
        except:
            pass
        card.clicked.connect(lambda: self.open_checkout(data))

        return card

    def open_checkout(self, data):
        dlg = CheckoutDialog(self, data, self.ctrl)
        if dlg.exec() == 1:
            # DELAY REFRESH TO PREVENT CRASH
            QTimer.singleShot(200, self.refresh)


class CheckoutDialog(QDialog):
    def __init__(self, parent, data, ctrl):
        super().__init__(parent)
        self.setWindowTitle(f"Checkout Room {data['room']}")
        self.setFixedSize(400, 550)
        self.ctrl = ctrl
        self.data = data

        # Calculate what is actually owed
        self.balance_due = int(data['final_balance'])

        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(30, 30, 30, 30)

        # Info Section
        l.addWidget(QLabel(f"Guest: {data['guest']}", styleSheet="font-size: 16px; font-weight: bold;"))
        l.addWidget(QLabel(f"Total Bill: ₱{data['total']:,}"))
        l.addWidget(QLabel(f"Already Paid: ₱{data['paid']:,}"))

        # Balance Display
        l.addWidget(QLabel("---------------------------------"))
        l.addWidget(QLabel(f"BALANCE DUE: ₱{self.balance_due:,}",
                           styleSheet="font-size: 24px; font-weight: 900; color: #C0392B;"))
        l.addWidget(QLabel("---------------------------------"))

        if self.balance_due > 0:
            l.addWidget(QLabel("Amount Tendered (Cash/Card):", styleSheet="font-weight:bold;"))

            # Input for Amount Tendered
            self.spin = QSpinBox()
            self.spin.setRange(0, 1000000)  # Allow large numbers
            self.spin.setValue(self.balance_due)  # Default to exact amount
            self.spin.setStyleSheet("""
                QSpinBox { font-size: 18px; padding: 10px; font-weight: bold; }
            """)
            self.spin.valueChanged.connect(self.calculate_change)
            l.addWidget(self.spin)

            self.cb_method = QComboBox()
            self.cb_method.addItems(["Cash", "Credit Card", "Debit Card"])
            self.cb_method.setStyleSheet(INPUT_STYLE)
            l.addWidget(self.cb_method)

            # Change Display
            self.lbl_change = QLabel("Change: ₱0")
            self.lbl_change.setStyleSheet("font-size: 18px; font-weight: bold; color: #27AE60; margin-top: 10px;")
            self.lbl_change.setAlignment(Qt.AlignmentFlag.AlignRight)
            l.addWidget(self.lbl_change)

        else:
            l.addWidget(QLabel("✅ Fully Paid", styleSheet="color: green; font-size: 18px; font-weight: bold;"))
            self.spin = None

        l.addStretch()

        btn = QPushButton("PROCESS CHECKOUT")
        btn.setStyleSheet(
            "QPushButton { background-color: #2C3E50; color: white; font-weight: bold; border-radius: 5px; padding: 15px; font-size: 14px; } QPushButton:hover { background-color: #34495E; }")
        btn.clicked.connect(self.process)
        l.addWidget(btn)

    def calculate_change(self):
        if not self.spin: return
        tendered = self.spin.value()
        change = tendered - self.balance_due

        if change < 0:
            self.lbl_change.setText(f"Short: ₱{abs(change):,}")
            self.lbl_change.setStyleSheet("font-size: 18px; font-weight: bold; color: #C0392B; margin-top: 10px;")
        else:
            self.lbl_change.setText(f"Change: ₱{change:,}")
            self.lbl_change.setStyleSheet("font-size: 18px; font-weight: bold; color: #27AE60; margin-top: 10px;")

    def process(self):
        try:
            tendered = self.spin.value() if self.spin else 0
            method = self.cb_method.currentText() if hasattr(self, 'cb_method') else "None"

            if self.balance_due > 0 and tendered < self.balance_due:
                QMessageBox.warning(self, "Insufficient Payment",
                                    f"The guest is short by ₱{self.balance_due - tendered:,}.\nPlease collect the full amount.")
                return

            # Show processing indicator
            self.setEnabled(False)
            QApplication.processEvents()  # Update UI

            res, msg = self.ctrl.process_checkout(self.data, tendered, method)

            self.setEnabled(True)

            if res:
                change = max(0, tendered - self.balance_due)
                success_msg = f"Checkout Successful!\n\nAmount Tendered: ₱{tendered:,}\nChange Due: ₱{change:,}\n\nReceipt has been saved to 'receipts' folder."
                QMessageBox.information(self, "Success", success_msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", f"Checkout failed:\n{msg}")

        except Exception as e:
            self.setEnabled(True)
            print(f"CRITICAL ERROR in checkout dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "System Error",
                                 f"An unexpected error occurred:\n{str(e)}\n\nPlease contact support if this persists.")


# ==========================================
# PAGE 6: HOUSEKEEPING
# ==========================================
class HousekeepingPage(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        l = QVBoxLayout(self)
        l.setContentsMargins(20, 20, 20, 20)
        l.addWidget(QLabel("Housekeeping & Room Status",
                           styleSheet="font-size: 24px; font-weight: 800; color: #2C3E50; margin-bottom: 10px;"))
        l.addWidget(QLabel(
            "Click on 'Dirty' (Orange) rooms to assign a cleaner.\nClick 'Cleaning' (Yellow) rooms to mark as Clean.",
            styleSheet="color: #7f8c8d; margin-bottom: 20px; font-style: italic;"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        content = QWidget()
        self.grid = QGridLayout(content)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(15)
        scroll.setWidget(content)
        l.addWidget(scroll)
        btn_refresh = QPushButton("Refresh Status")
        btn_refresh.setStyleSheet(
            "background: #2C3E50; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh)
        l.addWidget(btn_refresh)
        self.refresh()

    def refresh(self):
        while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
        rooms = self.ctrl.get_map_data()
        r, c = 0, 0
        for rm in rooms:
            self.grid.addWidget(self.create_card(rm), r, c)
            c += 1
            if c > 5: c = 0; r += 1

    def create_card(self, rm):
        room_num, status, desc = rm[0], rm[1], rm[2]
        if status == 'Dirty':
            color = "#E67E22"
            hover = "#D35400"
            border = "#D35400"
            cursor = Qt.CursorShape.PointingHandCursor
        elif status == 'Cleaning':
            color = "#F1C40F"
            hover = "#F39C12"
            border = "#D68910"
            cursor = Qt.CursorShape.PointingHandCursor
        elif status == 'Occupied':
            color = "#2ECC71"
            hover = "#2ECC71"
            border = "#27AE60"
            cursor = Qt.CursorShape.ForbiddenCursor
        else:  # Vacant
            color = "#95A5A6"
            hover = "#95A5A6"
            border = "#7F8C8D"
            cursor = Qt.CursorShape.ForbiddenCursor
        btn = QPushButton(f"{room_num}\n{desc}\n{status}")
        btn.setFixedSize(120, 90)
        btn.setCursor(cursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; border-radius: 8px; font-weight: bold; border: 2px solid {border}; }} QPushButton:hover {{ background-color: {hover}; }}")
        if status == 'Dirty':
            btn.clicked.connect(lambda checked, rn=room_num: self.open_assign_dialog(rn))
        elif status == 'Cleaning':
            btn.clicked.connect(lambda checked, rn=room_num: self.finish_cleaning(rn))
        else:
            btn.setDisabled(True)
            btn.setStyleSheet(btn.styleSheet() + "QPushButton { opacity: 0.8; }")
        return btn

    def open_assign_dialog(self, room_num):
        dlg = AssignCleanerDialog(self, room_num, self.ctrl)
        if dlg.exec() == 1: self.refresh()

    def finish_cleaning(self, room_num):
        if QMessageBox.question(self, "Confirm",
                                f"Room {room_num} cleaning finished? (Mark Vacant)") == QMessageBox.StandardButton.Yes:
            res, msg = self.ctrl.finish_cleaning(room_num)
            if res: QMessageBox.information(self, "Success", msg)
            self.refresh()


class AssignCleanerDialog(QDialog):
    def __init__(self, parent, room_num, ctrl):
        super().__init__(parent)
        self.setWindowTitle(f"Assign Cleaner for Room {room_num}")
        self.setFixedSize(350, 200)
        self.ctrl = ctrl
        self.room_num = room_num
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Select Available Cleaner:", styleSheet="font-weight:bold; font-size:14px;"))
        self.cb = QComboBox()
        cleaners = [c[1] for c in self.ctrl.get_available_cleaners()]
        self.cb.addItems(cleaners)
        self.cb.setStyleSheet(INPUT_STYLE)
        l.addWidget(self.cb)
        if not cleaners:
            l.addWidget(QLabel("No available cleaners!", styleSheet="color:red;"))
            self.cb.setDisabled(True)
        btn = QPushButton("Assign and Start Cleaning")
        btn.setStyleSheet(BTN_STYLE)
        btn.clicked.connect(self.assign)
        if not cleaners: btn.setDisabled(True)
        l.addWidget(btn)

    def assign(self):
        emp = self.cb.currentText()
        res, msg = self.ctrl.assign_cleaner(self.room_num, emp)
        if res:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)