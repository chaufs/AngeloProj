from Model.m_admin import AdminModel
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QSizeF
from datetime import datetime, timedelta
import calendar


class AdminController:
    def __init__(self):
        self.model = AdminModel()

    # 🟢 DASHBOARD: New Stats Logic
    def get_dashboard_stats(self):
        current_year = datetime.now().year

        # 1. Total Bookings
        bookings_count = len(self.model.get_all_bookings())

        # 2. Total Revenue (Current Year)
        total_revenue = self.model.get_total_revenue_year(current_year)

        # 3. Total Employees
        employees_count = self.model.get_employee_count()

        # 4. Total Rooms (Filler for 4th card)
        rooms_count = len(self.model.get_all_rooms())

        return {
            'bookings': bookings_count,
            'revenue': total_revenue,
            'employees': employees_count,
            'rooms': rooms_count,
            'year': current_year
        }

    # --- EXISTING METHODS ---
    def get_available_dates(self):
        raw_dates = self.model.get_payment_dates()
        data = {}
        for d_str in raw_dates:
            try:
                date_part = d_str.split(' ')[0]
                year, month, day = date_part.split('-')
                if year not in data: data[year] = set()
                data[year].add(month)
            except:
                continue
        final_data = {}
        for y in sorted(data.keys(), reverse=True):
            final_data[y] = sorted(list(data[y]))
        return final_data

    def get_current_month_stats(self):
        now = datetime.now()
        year = now.year
        month = now.month
        last_day = calendar.monthrange(year, month)[1]
        s_date = f"{year}-{month:02d}-01"
        e_date = f"{year}-{month:02d}-{last_day}"
        data = self.get_analytics(s_date, e_date)
        return {'total': data['rev_room'] + data['rev_svc'], 'room': data['rev_room'], 'service': data['rev_svc'],
                'month_name': calendar.month_name[month]}

    def get_analytics(self, s_date, e_date):
        payments, bookings, services = self.model.get_analytics_data()
        all_rooms_data = self.model.get_all_rooms()
        pay_filt = [p for p in payments if s_date <= str(p[7]).split(' ')[0] <= e_date]
        book_filt = [b for b in bookings if s_date <= str(b[1]) <= e_date]
        svc_filt = [s for s in services if s[1] and s_date <= str(s[1]).split(' ')[0] <= e_date]
        rev_room = sum(p[3] for p in pay_filt)
        rev_svc = sum(p[4] for p in pay_filt)
        room_counts = {}
        unique_types = set(r[1] for r in all_rooms_data if r[1])
        if not unique_types: unique_types = {"Single", "Double", "Queen", "King", "Suite"}
        for t in unique_types: room_counts[t] = 0
        for b in book_filt:
            rtype = b[0] or "Unknown"
            room_counts[rtype] = room_counts.get(rtype, 0) + 1
        svc_counts = {}
        history_services = set(s[0] for s in services if s[0])
        default_services = {"Breakfast", "Lunch Set", "Dinner", "Massage", "Laundry", "Transport", "Extra Bed", "Spa"}
        all_known = history_services.union(default_services)
        for name in all_known: svc_counts[name] = 0
        for s in svc_filt:
            sname = s[0] or "Misc"
            qty = s[3] if len(s) > 3 else 1
            svc_counts[sname] = svc_counts.get(sname, 0) + qty
        return {'rev_room': rev_room, 'rev_svc': rev_svc, 'room_counts': room_counts, 'svc_counts': svc_counts}

    def export_report(self, year, month_num):
        if month_num == "All":
            start_date = f"{year}-01-01";
            end_date = f"{year}-12-31";
            period_label = f"Annual Report - {year}"
        else:
            import calendar
            last_day = calendar.monthrange(int(year), int(month_num))[1]
            start_date = f"{year}-{month_num}-01";
            end_date = f"{year}-{month_num}-{last_day}"
            period_label = f"{calendar.month_name[int(month_num)]} {year}"

        all_data = self.model.get_report_data_comprehensive()

        def in_range(date_str):
            try:
                return start_date <= str(date_str).split(' ')[0] <= end_date
            except:
                return False

        payments = [p for p in all_data['payments'] if in_range(p[7])]
        bookings = [b for b in all_data['bookings'] if in_range(b[3])]
        services = [s for s in all_data['services'] if in_range(s[2])]
        housekeeping = [h for h in all_data['housekeeping'] if in_range(h[2])]
        activity_logs = [l for l in all_data['logs'] if in_range(l[2])]

        total_rev = sum(p[5] for p in payments)
        header_color = "#E67E22"  # Orange for titles
        table_header = "#2C3E50"  # Dark Blue for tables

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 10px; }}
                h1 {{ color: {header_color}; margin-bottom: 5px; }}
                h3 {{ color: #555; margin-top: 0; }}
                h2 {{ color: {header_color}; border-bottom: 2px solid {header_color}; padding-bottom: 5px; margin-top: 25px; }}
                th {{ background-color: {table_header}; color: white; padding: 6px; font-weight: bold; text-align: left; }}
                td {{ padding: 6px; color: #333; border-bottom: 1px solid #eee; }}
                .total-box {{ background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <center>
                <h1>HOTELLA FULL REPORT</h1>
                <h3>{period_label}</h3>
            </center>

            <div class="total-box">
                <span style="font-size: 12px; font-weight: bold; color: {table_header};">TOTAL REVENUE: </span>
                <span style="font-size: 16px; font-weight: bold; color: {header_color};">₱{total_rev:,}</span>
                <br>
                <span style="font-size: 10px;">Transactions: {len(payments)} | New Bookings: {len(bookings)}</span>
            </div>

            <h2>1. Revenue / Payments</h2>
            <table width="100%" border="0" cellspacing="0" cellpadding="4">
                <tr><th>ID</th><th>Guest</th><th>Amount</th><th>Method</th><th>Date</th></tr>
        """
        for p in payments:
            html += f"<tr><td>{p[1]}</td><td>{p[2]}</td><td>₱{p[5]:,}</td><td>{p[6]}</td><td>{p[7]}</td></tr>"
        if not payments: html += "<tr><td colspan='5' align='center'>No Data</td></tr>"
        html += "</table>"

        html += f"""
            <h2>2. Services Availed</h2>
            <table width="100%" border="0" cellspacing="0" cellpadding="4">
                <tr><th>Service</th><th>Guest Name</th><th>Room</th><th>Qty</th><th>Price</th><th>Date</th></tr>
        """
        for s in services:
            guest_name = s[5] if s[5] else "Unknown"
            html += f"<tr><td>{s[0]}</td><td>{guest_name}</td><td>{s[4]}</td><td>{s[3]}</td><td>₱{s[1]:,}</td><td>{s[2]}</td></tr>"
        if not services: html += "<tr><td colspan='6' align='center'>No Data</td></tr>"
        html += "</table>"

        html += f"""
            <h2>3. Booking History</h2>
            <table width="100%" border="0" cellspacing="0" cellpadding="4">
                <tr><th>ID</th><th>Name</th><th>Type</th><th>Status</th><th>Date</th></tr>
        """
        for b in bookings:
            html += f"<tr><td>B{b[0]:05d}</td><td>{b[1]}</td><td>{b[2]}</td><td>{b[6]}</td><td>{b[3]}</td></tr>"
        if not bookings: html += "<tr><td colspan='5' align='center'>No Data</td></tr>"
        html += "</table>"

        html += f"""
            <h2>4. Booking Activity Log</h2>
            <table width="100%" border="0" cellspacing="0" cellpadding="4">
                <tr><th>Timestamp</th><th>Booking ID</th><th>Guest</th><th>Action</th><th>Staff</th></tr>
        """
        for log in activity_logs:
            html += f"<tr><td>{log[2]}</td><td>{log[3]}</td><td>{log[0]}</td><td>{log[1]}</td><td>{log[4]}</td></tr>"
        if not activity_logs: html += "<tr><td colspan='5' align='center'>No Data</td></tr>"
        html += "</table>"

        html += f"""
            <h2>5. Housekeeping Logs</h2>
            <table width="100%" border="0" cellspacing="0" cellpadding="4">
                <tr><th>Room</th><th>Action</th><th>Time</th></tr>
        """
        for h in housekeeping:
            html += f"<tr><td>{h[0]}</td><td>{h[1]}</td><td>{h[2]}</td></tr>"
        if not housekeeping: html += "<tr><td colspan='3' align='center'>No Data</td></tr>"
        html += "</table>"

        html += """<br><br><div style="text-align:center; color:gray;">Generated by Hotella Management System</div></body></html>"""

        fn, _ = QFileDialog.getSaveFileName(None, "Save Report", f"Full_Report_{year}_{month_num}.pdf",
                                            "PDF Files (*.pdf)")
        if fn:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(fn)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            doc = QTextDocument()
            doc.setHtml(html)
            doc.setPageSize(QSizeF(printer.pageRect(QPrinter.Unit.Point).size()))
            doc.print(printer)
            return True, "Full Report saved successfully!"
        return False, "Export cancelled."

    def get_employees(self):
        return self.model.get_all_employees()

    def add_new_employee(self, n, r, c, u, p):
        if not n or not r: return False, "Name/Role req."
        if r == "Manager": return False, "Cannot create Manager."
        needs_acc = (r == "Receptionist")
        if needs_acc and (not u or not p): return False, "User/Pass req."
        eid = self.model.add_employee(n, r, c)
        if not eid: return False, "DB Error"
        if needs_acc: self.model.create_user_account(u, p, 'staff', eid)
        return True, "Success"

    def set_employee_status(self, eid, s):
        return self.model.update_employee_status(eid, s), "Updated"

    def remove_employee(self, eid):
        return self.model.delete_employee(eid), "Removed"

    def get_room_history(self, r):
        return self.model.get_room_history_data(r)

    def get_activity_logs(self):
        return self.model.get_all_activity_logs()

    def set_room_status(self, r, s):
        if s == "Maintenance" and self.model.check_active_bookings(r): return False, "Room Busy"
        return self.model.update_room_status(r, s), "Updated"

    def change_room_type(self, r, t):
        if self.model.check_active_bookings(r): return False, "Room Busy"
        return self.model.update_room_type(r, t), "Updated"

    def get_filtered_bookings(self, s, e):
        return [b for b in self.model.get_all_bookings() if s <= (b[6] or "") <= e]

    def get_all_rooms(self):
        return self.model.get_all_rooms()

    def get_all_services(self):
        return self.model.get_all_services()

    def get_all_payments(self):
        return self.model.get_all_payments()

    def save_room(self, is_new, d, oid=None):
        try:
            if is_new:
                self.model.add_room(d)
            else:
                self.model.update_room(oid, d)
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def delete_room(self, r):
        self.model.delete_room(r)

    def delete_booking(self, e):
        self.model.delete_booking(e)

    def delete_service(self, s):
        self.model.delete_service(s)