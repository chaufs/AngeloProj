from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit,
                             QMessageBox, QDialog, QFormLayout, QLineEdit, QTabWidget, QAbstractItemView, QFileDialog,
                             QComboBox, QSpinBox, QScrollArea, QGroupBox)
from PyQt6.QtCore import Qt, QDate, QTimer, QTime, pyqtSignal
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from datetime import datetime
import calendar
# --- STYLES ---
TABLE_STYLE = """
    QTableWidget { background-color: white; color: #2C3E50; border: 1px solid #BDC3C7; border-radius: 5px; gridline-color: #ECF0F1; font-size: 13px; }
    QHeaderView::section { background-color: #2C3E50; color: white; font-weight: bold; border: none; padding: 10px; font-size: 13px; }
    QTableWidget::item { padding: 5px; }
    QTableWidget::item:hover { background-color: #F5F6FA; }
"""
# 🟢 Helper function to make tables non-clickable/non-editable
def make_table_readonly(table):
    """Make a table non-clickable and non-editable"""
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
INPUT_STYLE = """
    QLineEdit, QComboBox, QSpinBox { 
        padding: 8px; 
        border: 1px solid #BDC3C7; 
        border-radius: 5px; 
        font-size: 13px; 
        background-color: white; 
        color: #2C3E50; 
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: white; color: #2C3E50;
        selection-background-color: #3498DB; selection-color: white;
        border: 1px solid #BDC3C7;
    }
"""
GROUP_STYLE = """
    QGroupBox { 
        font-weight: bold; border: 1px solid #BDC3C7; margin-top: 10px; 
        color: #2C3E50; background-color: white; border-radius: 5px;
    } 
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
"""
MESSAGEBOX_STYLE = """
    QMessageBox { background-color: white; color: #2C3E50; }
    QMessageBox QLabel { color: #2C3E50; font-weight: bold; font-size: 14px; }
    QMessageBox QPushButton { background-color: #3498DB; color: white; padding: 6px 20px; border-radius: 4px; font-weight: bold; }
    QMessageBox QPushButton:hover { background-color: #2980B9; }
"""
class ClickableFrame(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, card_type, parent=None):
        super().__init__(parent)
        self.card_type = card_type
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, event):
        self.clicked.emit(self.card_type)
        super().mousePressEvent(event)
class AdminHome(QWidget):
    switch_tab_signal = pyqtSignal(str)
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True);
        self.setStyleSheet("background-color: #F4F6F9;")
        self.layout = QVBoxLayout();
        self.layout.setContentsMargins(30, 30, 30, 30);
        self.layout.setSpacing(20);
        self.setLayout(self.layout)
        self.timer = QTimer();
        self.timer.timeout.connect(self.update_clock);
        self.timer.start(1000);
        self.refresh_data()
    def refresh_data(self):
        while self.layout.count(): self.layout.takeAt(0).widget().deleteLater()
        self.create_header()
        self.create_stats()
        self.layout.addStretch()
    def create_header(self):
        f = QFrame();
        f.setFixedHeight(100);
        f.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E67E22, stop:1 #D35400); border-radius: 15px;")
        h = QHBoxLayout(f);
        h.setContentsMargins(25, 0, 25, 0)
        h.addWidget(QLabel("Hotella Dashboard",
                           styleSheet="font-size: 28px; font-weight: 800; color: white; background: transparent;"));
        h.addStretch()
        self.time_lbl = QLabel(styleSheet="font-size: 24px; color: white; background: transparent; font-weight: bold;")
        self.date_lbl = QLabel(styleSheet="font-size: 14px; color: white; background: transparent;")
        r = QVBoxLayout();
        r.setAlignment(Qt.AlignmentFlag.AlignRight);
        r.addWidget(self.time_lbl);
        r.addWidget(self.date_lbl);
        h.addLayout(r);
        self.update_clock();
        self.layout.addWidget(f)
    def update_clock(self):
        if hasattr(self, 'time_lbl'): self.time_lbl.setText(
            QTime.currentTime().toString('hh:mm:ss AP')); self.date_lbl.setText(
            datetime.now().strftime('%A, %B %d, %Y'))
    def create_stats(self):
        gl = QGridLayout();
        gl.setSpacing(20)
        stats = self.ctrl.get_dashboard_stats()
        cards_data = [
            ("TOTAL BOOKINGS", stats.get('bookings', 0), "#3498DB", "bookings"),
            (f"REVENUE ({stats.get('year')})", f"₱{stats.get('revenue', 0):,}", "#2ECC71", "analytics"),
            ("TOTAL EMPLOYEES", stats.get('employees', 0), "#E67E22", "employees"),
            ("TOTAL ROOMS", stats.get('rooms', 0), "#9B59B6", "rooms")
        ]
        for i, (label, value, color, c_type) in enumerate(cards_data):
            card = ClickableFrame(c_type)
            card.setFixedHeight(140)
            card.setStyleSheet(f"background-color: {color}; border-radius: 10px; color: white;")
            card.clicked.connect(self.switch_tab_signal.emit)
            cl = QGridLayout(card)
            cl.setContentsMargins(20, 20, 20, 20)
            lbl_title = QLabel(str(label))
            lbl_title.setStyleSheet(
                "font-size: 13px; font-weight: bold; background: transparent; color: rgba(255,255,255,0.9);")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet("font-size: 40px; font-weight: 800; background: transparent;")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            lbl_val.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            cl.addWidget(lbl_title, 0, 0)
            cl.addWidget(lbl_val, 1, 0)
            gl.addWidget(card, i // 2, i % 2)
        self.layout.addLayout(gl)
class AdminManagement(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True);
        self.setStyleSheet("background-color: #F4F6F9;")
        layout = QVBoxLayout();
        layout.setContentsMargins(20, 20, 20, 20)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #BDC3C7; background: white; border-radius: 5px; }
            QTabBar::tab { background: #E0E0E0; color: #555; padding: 10px 25px; font-weight: bold; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
            QTabBar::tab:selected { background: #2C3E50; color: white; border-bottom: 3px solid #FDB515; }
        """)
        # 🟢 REMOVED: Analytics Tab from here
        self.pages = [
            BookingTab(ctrl),
            RoomTab(ctrl),
            EmployeesTab(ctrl),
            # Analytics is removed from here
            RoomMaintenanceTab(ctrl),
            RoomHistoryTab(ctrl),
            ServicesReportTab(ctrl),
            PaymentReportTab(ctrl),
            SystemLogsTab(ctrl)
        ]
        titles = ["Bookings", "Rooms", "Employees", "Maintenance", "History", "Services", "Payments", "System Logs"]
        for p, t in zip(self.pages, titles): self.tabs.addTab(p, t)
        layout.addWidget(self.tabs);
        self.setLayout(layout)
    def refresh_data(self):
        for p in self.pages:
            if hasattr(p, 'load'): p.load()
            if hasattr(p, 'refresh_data'): p.refresh_data()
    # 🟢 UPDATED: Navigate to correct tab index
    def navigate_to(self, tab_name):
        map_name = {
            "bookings": 0,
            "rooms": 1,
            "employees": 2
        }
        if tab_name in map_name:
            self.tabs.setCurrentIndex(map_name[tab_name])
class EmployeesTab(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        layout = QHBoxLayout(self)
        self.t = QTableWidget(0, 6)
        self.t.setHorizontalHeaderLabels(["ID", "Name", "Role", "Contact", "Status", "Username"])
        self.t.setStyleSheet(TABLE_STYLE)
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.t, stretch=2)
        ctrl_panel = QVBoxLayout()
        gb_add = QGroupBox("Add New Employee")
        gb_add.setStyleSheet(GROUP_STYLE)
        fl = QVBoxLayout(gb_add)
        fl.setSpacing(10)
        self.inp_name = QLineEdit(placeholderText="Full Name");
        self.inp_name.setStyleSheet(INPUT_STYLE)
        self.inp_contact = QLineEdit(placeholderText="Contact Number");
        self.inp_contact.setStyleSheet(INPUT_STYLE)
        self.cb_role = QComboBox()
        self.cb_role.addItems(["Cleaner", "Receptionist"])
        self.cb_role.setStyleSheet(INPUT_STYLE)
        self.cb_role.currentTextChanged.connect(self.toggle_account_fields)
        fl.addWidget(QLabel("Role:", styleSheet="color:#555; font-weight:bold;"));
        fl.addWidget(self.cb_role)
        fl.addWidget(self.inp_name);
        fl.addWidget(self.inp_contact)
        self.gb_account = QGroupBox("System Login")
        self.gb_account.setStyleSheet("border:none; margin-top:5px;")
        gl = QVBoxLayout(self.gb_account)
        gl.setContentsMargins(0, 0, 0, 0)
        self.inp_user = QLineEdit(placeholderText="Username");
        self.inp_user.setStyleSheet(INPUT_STYLE)
        self.inp_pass = QLineEdit(placeholderText="Password");
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password);
        self.inp_pass.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.inp_user);
        gl.addWidget(self.inp_pass)
        fl.addWidget(self.gb_account)
        self.gb_account.hide()
        btn_add = QPushButton("Add Employee")
        btn_add.setStyleSheet(
            "background: #27AE60; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_add.clicked.connect(self.add_employee)
        fl.addWidget(btn_add)
        ctrl_panel.addWidget(gb_add)
        gb_act = QGroupBox("Manage Status")
        gb_act.setStyleSheet(GROUP_STYLE)
        al = QVBoxLayout(gb_act)
        lbl_hint = QLabel("To remove access, set status to Inactive.\nDo not delete employees to preserve history.",
                          styleSheet="color: #7F8C8D; font-size: 11px; font-style: italic;")
        lbl_hint.setWordWrap(True)
        al.addWidget(lbl_hint)
        btn_active = QPushButton("Set Active")
        btn_active.setStyleSheet("background: #3498DB; color: white; padding: 10px; font-weight: bold;")
        btn_active.clicked.connect(lambda: self.set_status("Active"))
        btn_inactive = QPushButton("Set Inactive")
        btn_inactive.setStyleSheet("background: #95A5A6; color: white; padding: 10px; font-weight: bold;")
        btn_inactive.clicked.connect(lambda: self.set_status("Inactive"))
        al.addWidget(btn_active);
        al.addWidget(btn_inactive)
        ctrl_panel.addWidget(gb_act)
        ctrl_panel.addStretch()
        layout.addLayout(ctrl_panel, stretch=1)
        self.toggle_account_fields(self.cb_role.currentText())
        self.load()
    def toggle_account_fields(self, role):
        if role == "Receptionist":
            self.gb_account.show()
        else:
            self.gb_account.hide();
            self.inp_user.clear();
            self.inp_pass.clear()
    def load(self):
        self.t.setRowCount(0)
        for e in self.ctrl.get_employees():
            r = self.t.rowCount();
            self.t.insertRow(r)
            self.t.setItem(r, 0, QTableWidgetItem(str(e[0])))
            self.t.setItem(r, 1, QTableWidgetItem(str(e[1])))
            self.t.setItem(r, 2, QTableWidgetItem(str(e[2])))
            self.t.setItem(r, 3, QTableWidgetItem(str(e[3])))
            status = str(e[4]) if e[4] else "Active"
            s_item = QTableWidgetItem(status)
            if status == "Inactive":
                s_item.setForeground(Qt.GlobalColor.red)
            elif status == "Active":
                s_item.setForeground(Qt.GlobalColor.green)
            elif status == "Busy":
                s_item.setForeground(Qt.GlobalColor.blue)
            self.t.setItem(r, 4, s_item)
            user_acc = e[5] if e[5] else "---"
            self.t.setItem(r, 5, QTableWidgetItem(str(user_acc)))
    def show_msg(self, title, txt, icon):
        msg = QMessageBox(self);
        msg.setWindowTitle(title);
        msg.setText(txt);
        msg.setIcon(icon);
        msg.setStyleSheet(
            MESSAGEBOX_STYLE);
        msg.exec()
    def add_employee(self):
        name = self.inp_name.text();
        role = self.cb_role.currentText();
        contact = self.inp_contact.text();
        user = self.inp_user.text();
        pwd = self.inp_pass.text()
        success, msg = self.ctrl.add_new_employee(name, role, contact, user, pwd)
        if success:
            self.show_msg("Success", msg,
                          QMessageBox.Icon.Information);
            self.inp_name.clear();
            self.inp_contact.clear();
            self.inp_user.clear();
            self.inp_pass.clear();
            self.load()
        else:
            self.show_msg("Error", msg, QMessageBox.Icon.Warning)
    def set_status(self, status):
        row = self.t.currentRow()
        if row < 0: return self.show_msg("Error", "Select an employee.", QMessageBox.Icon.Warning)
        res, msg = self.ctrl.set_employee_status(self.t.item(row, 0).text(), status)
        if res:
            self.load()
        else:
            self.show_msg("Error", msg, QMessageBox.Icon.Warning)
class RoomMaintenanceTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        layout = QHBoxLayout(self)
        self.t = QTableWidget(0, 3);
        self.t.setHorizontalHeaderLabels(["Room No", "Type", "Status"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        layout.addWidget(self.t, stretch=2)
        ctrl_panel = QVBoxLayout()
        gb1 = QGroupBox("Availability Control");
        gb1.setStyleSheet(GROUP_STYLE);
        gl1 = QVBoxLayout(gb1)
        btn_maint = QPushButton("Set to Maintenance");
        btn_maint.setStyleSheet("background: #E74C3C; color: white; padding: 10px; font-weight: bold;");
        btn_maint.clicked.connect(lambda: self.set_status("Maintenance"))
        btn_avail = QPushButton("Set Available");
        btn_avail.setStyleSheet("background: #27AE60; color: white; padding: 10px; font-weight: bold;");
        btn_avail.clicked.connect(lambda: self.set_status("Vacant"))
        gl1.addWidget(btn_maint);
        gl1.addWidget(btn_avail);
        ctrl_panel.addWidget(gb1)
        gb2 = QGroupBox("Upgrade / Change Room");
        gb2.setStyleSheet(GROUP_STYLE);
        gl2 = QVBoxLayout(gb2)
        gl2.addWidget(QLabel("New Room Type:", styleSheet="color: #2C3E50; font-weight: bold;"))
        self.cb_type = QComboBox();
        self.cb_type.addItems(["Single", "Double", "Queen", "King", "Suite"]);
        self.cb_type.setStyleSheet(INPUT_STYLE);
        gl2.addWidget(self.cb_type)
        btn_update = QPushButton("Update Type");
        btn_update.setStyleSheet("background: #3498DB; color: white; padding: 10px; font-weight: bold;");
        btn_update.clicked.connect(self.update_type)
        gl2.addWidget(btn_update);
        ctrl_panel.addWidget(gb2);
        ctrl_panel.addStretch();
        layout.addLayout(ctrl_panel, stretch=1);
        self.selected_room = None;
        self.load()
    def load(self):
        self.t.setRowCount(0);
        self.selected_room = None
        for r in self.ctrl.get_all_rooms():
            row = self.t.rowCount();
            self.t.insertRow(row);
            self.t.setItem(row, 0, QTableWidgetItem(str(r[0])));
            self.t.setItem(row, 1, QTableWidgetItem(str(r[1])));
            self.t.setItem(row, 2, QTableWidgetItem(str(r[2])))
            if str(r[2]) == "Maintenance":
                for i in range(3): self.t.item(row, i).setBackground(Qt.GlobalColor.lightGray)
    def on_row_click(self, row, col):
        self.selected_room = self.t.item(row, 0).text();
        self.cb_type.setCurrentText(self.t.item(row, 1).text())
    def show_message(self, title, text, icon):
        msg = QMessageBox(self);
        msg.setWindowTitle(title);
        msg.setText(text);
        msg.setIcon(icon);
        msg.setStyleSheet(
            MESSAGEBOX_STYLE);
        msg.exec()
    def set_status(self, status):
        if not self.selected_room: return self.show_message("Error", "Select room.", QMessageBox.Icon.Warning)
        s, m = self.ctrl.set_room_status(self.selected_room, status)
        if s:
            self.show_message("Success", m, QMessageBox.Icon.Information);
            self.load()
        else:
            self.show_message("Blocked", m, QMessageBox.Icon.Warning)
    def update_type(self):
        if not self.selected_room: return self.show_message("Error", "Select room.", QMessageBox.Icon.Warning)
        s, m = self.ctrl.change_room_type(self.selected_room, self.cb_type.currentText())
        if s:
            self.show_message("Success", m, QMessageBox.Icon.Information);
            self.load()
        else:
            self.show_message("Blocked", m, QMessageBox.Icon.Warning)
class BookingTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setLayout(QVBoxLayout())
        self.t = QTableWidget(0, 7);
        self.t.setHorizontalHeaderLabels(["ID", "Name", "Email", "Phone", "Addr", "Type", "Date"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        self.layout().addWidget(self.t);
        self.load()
    def load(self):
        self.t.setRowCount(0)
        for b in self.ctrl.get_filtered_bookings("2020-01-01", "2030-12-31"):
            r = self.t.rowCount();
            self.t.insertRow(r);
            self.t.setItem(r, 0, QTableWidgetItem(f"B{b[0]:05d}"))
            for i in range(1, 7): self.t.setItem(r, i, QTableWidgetItem(str(b[i])))
class RoomTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setLayout(QVBoxLayout())
        self.t = QTableWidget(0, 3);
        self.t.setHorizontalHeaderLabels(["No", "Desc", "Status"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        self.layout().addWidget(self.t);
        btn = QPushButton("Add Room");
        btn.clicked.connect(self.add);
        self.layout().addWidget(btn);
        self.load()
    def load(self):
        self.t.setRowCount(0)
        for r in self.ctrl.get_all_rooms():
            row = self.t.rowCount();
            self.t.insertRow(row);
            [self.t.setItem(row, i, QTableWidgetItem(str(r[i]))) for i in range(3)]
    def add(self):
        d = QDialog(self);
        f = QFormLayout(d);
        n = QLineEdit();
        de = QLineEdit();
        s = QLineEdit("Vacant");
        n.setStyleSheet(INPUT_STYLE);
        de.setStyleSheet(INPUT_STYLE);
        s.setStyleSheet(INPUT_STYLE);
        f.addRow("No", n);
        f.addRow("Desc", de);
        f.addRow("Stat", s);
        b = QPushButton("Save");
        b.clicked.connect(
            lambda: [self.ctrl.save_room(True, [n.text(), de.text(), s.text()]), d.accept(), self.load()]);
        f.addRow(b);
        d.exec()
class RoomHistoryTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        l = QVBoxLayout(self);
        h = QHBoxLayout();
        l_lbl = QLabel("Enter Room Number:", styleSheet="color:#2C3E50; font-weight:bold;")
        self.inp = QLineEdit(placeholderText="e.g. 101");
        self.inp.setStyleSheet(INPUT_STYLE)
        btn = QPushButton("Search History");
        btn.setStyleSheet("background:#3498DB; color:white; padding:8px; border-radius:5px; font-weight:bold;");
        btn.clicked.connect(self.search);
        h.addWidget(l_lbl);
        h.addWidget(self.inp);
        h.addWidget(btn);
        l.addLayout(h);
        self.t = QTableWidget(0, 6);
        self.t.setHorizontalHeaderLabels(["Booking ID", "Guest Name", "Date", "Duration", "Status", "Booked By"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        l.addWidget(self.t)
    def search(self):
        rid = self.inp.text().strip();
        if not rid: return
        self.t.setRowCount(0);
        history = self.ctrl.get_room_history(rid)
        if not history: return
        for h in history:
            r = self.t.rowCount();
            self.t.insertRow(r);
            self.t.setItem(r, 0, QTableWidgetItem(f"B{h[0]:05d}"));
            self.t.setItem(r, 1, QTableWidgetItem(str(h[1])));
            self.t.setItem(r, 2, QTableWidgetItem(str(h[2])));
            self.t.setItem(r, 3, QTableWidgetItem(f"{h[3]} Days"));
            self.t.setItem(r, 4, QTableWidgetItem(str(h[4])));
            self.t.setItem(r, 5, QTableWidgetItem(str(h[5])))
    def load(self):
        pass
class SystemLogsTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setLayout(QVBoxLayout());
        self.t = QTableWidget(0, 5);
        self.t.setHorizontalHeaderLabels(["Booking ID", "Guest", "Action", "Performed By", "Timestamp"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        self.layout().addWidget(self.t);
        self.load()
    def load(self):
        self.t.setRowCount(0);
        logs = self.ctrl.get_activity_logs()
        for log in logs:
            r = self.t.rowCount();
            self.t.insertRow(r);
            bid = log[1];
            guest = log[2];
            action = log[3];
            time = str(log[4]);
            staff = log[5] if len(log) > 5 else "---"
            self.t.setItem(r, 0, QTableWidgetItem(str(bid)));
            self.t.setItem(r, 1, QTableWidgetItem(str(guest)));
            self.t.setItem(r, 2, QTableWidgetItem(str(action)));
            self.t.setItem(r, 3, QTableWidgetItem(str(staff)));
            self.t.setItem(r, 4, QTableWidgetItem(str(time)))
class ServicesReportTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setLayout(QVBoxLayout());
        self.t = QTableWidget(0, 5);
        self.t.setHorizontalHeaderLabels(["Date", "ID", "Room", "Service", "Price"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        self.layout().addWidget(self.t);
        self.load()
    def load(self):
        self.t.setRowCount(0)
        for s in self.ctrl.get_all_services():
            r = self.t.rowCount();
            self.t.insertRow(r);
            items = [str(s[5]), s[1], s[2], s[3], f"₱{s[4]}"];
            for i, v in enumerate(items): self.t.setItem(r, i, QTableWidgetItem(str(v)))
class PaymentReportTab(QWidget):
    def __init__(self, ctrl):
        super().__init__();
        self.ctrl = ctrl;
        self.setLayout(QVBoxLayout());
        self.t = QTableWidget(0, 10);
        self.t.setHorizontalHeaderLabels(
            ["ID", "BookID", "Guest", "Room$", "Svc$", "Total", "Method", "Date", "Staff", "Remark"]);
        self.t.setStyleSheet(TABLE_STYLE);
        make_table_readonly(self.t)
        self.t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        self.layout().addWidget(self.t);
        self.load()
    def load(self):
        self.t.setRowCount(0)
        for p in self.ctrl.get_all_payments():
            r = self.t.rowCount();
            self.t.insertRow(r);
            processed_by = p[10] if len(p) > 10 else "---";
            remarks = p[11] if len(p) > 11 else "Payment"
            items = [p[0], p[1], p[2], p[3], p[4], p[5], p[6], str(p[7]), processed_by, remarks]
            for i, v in enumerate(items): self.t.setItem(r, i, QTableWidgetItem(str(v)))
class AdminSummary(QWidget):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self.available_data = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #F4F6F9;")
        self.figures = {}
        self.plt = None
        self.MaxNLocator = None
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)
        self.setup_header()
        self.setup_financial_banner()
        self.setup_content()
        self.load_charts_module()
        self.populate_filters()
    def load_charts_module(self):
        try:
            import matplotlib
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FC
            from matplotlib.figure import Figure as Fig
            import matplotlib.pyplot as plt
            from matplotlib.ticker import MaxNLocator
            self.plt = plt
            self.FigureCanvas = FC
            self.Figure = Fig
            self.MaxNLocator = MaxNLocator
        except ImportError:
            pass
    def setup_header(self):
        h = QHBoxLayout()
        h.addWidget(QLabel("Analytics Dashboard", styleSheet="font-size: 24px; font-weight: 800; color: #2C3E50;"))
        h.addStretch()
        self.cb_year = QComboBox();
        self.cb_year.setStyleSheet(INPUT_STYLE)
        self.cb_year.currentTextChanged.connect(self.on_year_changed)
        self.cb_month = QComboBox();
        self.cb_month.setStyleSheet(INPUT_STYLE)
        self.cb_month.currentIndexChanged.connect(self.load_data)
        btn_pdf = QPushButton("Export PDF")
        btn_pdf.setStyleSheet(
            "background: #E67E22; color: white; padding: 5px 15px; font-weight: bold; border-radius: 5px;")
        btn_pdf.clicked.connect(self.export_pdf)
        h.addWidget(QLabel("Year:", styleSheet="color:#555; font-weight:bold;"))
        h.addWidget(self.cb_year)
        h.addWidget(QLabel("Month:", styleSheet="color:#555; font-weight:bold;"))
        h.addWidget(self.cb_month)
        h.addWidget(btn_pdf)
        self.main_layout.addLayout(h)
    def setup_financial_banner(self):
        self.banner = QFrame()
        self.banner.setFixedHeight(90)
        self.banner.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #BDC3C7;")
        layout = QHBoxLayout(self.banner)
        layout.setContentsMargins(20, 10, 20, 10)
        self.lbl_month_name = QLabel("Current Overview")
        self.lbl_month_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #7F8C8D;")
        layout.addWidget(self.lbl_month_name)
        layout.addStretch()
        self.lbl_room_rev = QLabel("Room Rev: ₱0")
        self.lbl_room_rev.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #27AE60; background: #EAFAF1; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.lbl_room_rev)
        self.lbl_svc_rev = QLabel("Service Rev: ₱0")
        self.lbl_svc_rev.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #F39C12; background: #FEF9E7; padding: 8px; border-radius: 5px;")
        layout.addWidget(self.lbl_svc_rev)
        self.lbl_total_rev = QLabel("TOTAL: ₱0")
        self.lbl_total_rev.setStyleSheet("font-size: 20px; font-weight: 800; color: #2C3E50; margin-left: 20px;")
        layout.addWidget(self.lbl_total_rev)
        self.main_layout.addWidget(self.banner)
    def update_financial_banner(self, rev_room, rev_svc, total):
        period = self.cb_month.currentText() + " " + self.cb_year.currentText()
        if self.cb_month.currentText() == "All":
            period = f"Annual Report {self.cb_year.currentText()}"
        self.lbl_month_name.setText(period)
        self.lbl_room_rev.setText(f"Room Rev: ₱{rev_room:,}")
        self.lbl_svc_rev.setText(f"Service Rev: ₱{rev_svc:,}")
        self.lbl_total_rev.setText(f"TOTAL: ₱{total:,}")
    def setup_content(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget()
        self.cl = QVBoxLayout(content)
        self.chart_grid = QGridLayout()  # Grid for charts
        self.chart_grid.setSpacing(15)
        self.cl.addLayout(self.chart_grid)
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
    def populate_filters(self):
        self.available_data = self.ctrl.get_available_dates()
        self.cb_year.blockSignals(True)
        self.cb_year.clear()
        years = sorted(self.available_data.keys(), reverse=True)
        if not years:
            self.cb_year.addItem(str(datetime.now().year))
            self.cb_year.blockSignals(False);
            self.on_year_changed(self.cb_year.currentText());
            return
        self.cb_year.addItems(years)
        # Select Current Year
        curr = str(datetime.now().year)
        if curr in years:
            self.cb_year.setCurrentText(curr)
        else:
            self.cb_year.setCurrentIndex(0)
        self.cb_year.blockSignals(False)
        self.on_year_changed(self.cb_year.currentText())
    def on_year_changed(self, year):
        self.cb_month.blockSignals(True)
        self.cb_month.clear()
        self.cb_month.addItem("All", userData=None)
        if year in self.available_data:
            import calendar
            for m in self.available_data[year]:
                self.cb_month.addItem(calendar.month_name[int(m)], userData=m)
        # Select Current Month
        curr = f"{datetime.now().month:02d}"
        idx = self.cb_month.findData(curr)
        if idx >= 0:
            self.cb_month.setCurrentIndex(idx)
        else:
            self.cb_month.setCurrentIndex(0)
        self.cb_month.blockSignals(False)
        self.load_data()
    def load_data(self):
        if not self.plt: return
        year = self.cb_year.currentText()
        month_idx = self.cb_month.currentData()
        if not year: return
        if month_idx:
            import calendar
            last = calendar.monthrange(int(year), int(month_idx))[1]
            s_date = f"{year}-{month_idx}-01";
            e_date = f"{year}-{month_idx}-{last}"
        else:
            s_date = f"{year}-01-01";
            e_date = f"{year}-12-31"
        data = self.ctrl.get_analytics(s_date, e_date)
        total = data['rev_room'] + data['rev_svc']
        self.update_financial_banner(data['rev_room'], data['rev_svc'], total)
        while self.chart_grid.count(): self.chart_grid.takeAt(0).widget().deleteLater()
        f1 = self.frame("Revenue Breakdown")
        self.pie(f1, data['rev_room'], data['rev_svc'])
        self.chart_grid.addWidget(f1, 0, 0)
        f2 = self.frame("Most Used Room Types")
        self.bar_rooms(f2, data['room_counts'])
        self.chart_grid.addWidget(f2, 0, 1)
        f3 = self.frame("Top Services Offered")
        self.bar_services(f3, data['svc_counts'])
        self.chart_grid.addWidget(f3, 1, 0, 1, 2)
    # 🔴 UPDATED: Fix unreadable message box
    def export_pdf(self):
        year = self.cb_year.currentText();
        month = self.cb_month.currentData() or "All"
        s, m = self.ctrl.export_report(year, month)
        # Create a custom message box to apply the stylesheet
        msg = QMessageBox(self)
        msg.setWindowTitle("Export")
        msg.setText(m)
        msg.setIcon(QMessageBox.Icon.Information if s else QMessageBox.Icon.Warning)
        msg.setStyleSheet(MESSAGEBOX_STYLE)  # Force readability style
        msg.exec()
    def frame(self, t):
        f = QFrame(styleSheet="background: white; border: 1px solid #BDC3C7; border-radius: 8px;")
        f.setMinimumHeight(350);
        l = QVBoxLayout(f)
        l.addWidget(QLabel(t, styleSheet="font-weight:bold; color:#2C3E50; border:none;"))
        return f
    def pie(self, f, r, s):
        if r == 0 and s == 0: f.layout().addWidget(QLabel("No Revenue Data")); return
        fig = self.Figure(figsize=(4, 4), dpi=100);
        ax = fig.add_subplot(111)
        ax.pie([r, s], labels=['Room Rev', 'Svc Rev'], autopct='%1.1f%%', colors=['#2ECC71', '#F1C40F'])
        c = self.FigureCanvas(fig);
        f.layout().addWidget(c);
        c.draw()
    def bar_rooms(self, f, d):
        if not d: f.layout().addWidget(QLabel("No Data")); return
        fig = self.Figure(figsize=(4, 4), dpi=100);
        ax = fig.add_subplot(111)
        ax.bar(d.keys(), d.values(), color='#3498DB')
        ax.set_ylabel("Bookings Count")
        if self.MaxNLocator: ax.yaxis.set_major_locator(self.MaxNLocator(integer=True))
        c = self.FigureCanvas(fig);
        f.layout().addWidget(c);
        c.draw()
    def bar_services(self, f, d):
        if not d: f.layout().addWidget(QLabel("No Data")); return
        fig = self.Figure(figsize=(8, 4), dpi=100);
        ax = fig.add_subplot(111)
        ax.bar(d.keys(), d.values(), color='#9B59B6')
        ax.set_ylabel("Quantity Sold")
        if self.MaxNLocator: ax.yaxis.set_major_locator(self.MaxNLocator(integer=True))
        c = self.FigureCanvas(fig);
        f.layout().addWidget(c);
        c.draw()
    def refresh_data(self):
        self.populate_filters()
    # 🟢 NEW: Called by Dashboard to auto-set defaults
    def set_annual_view(self):
        current_year = str(datetime.now().year)
        self.cb_year.setCurrentText(current_year)
        self.cb_month.setCurrentIndex(0)  # "All"
        self.load_data()