from Model.m_staff import StaffModel
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageSize
import os


class StaffController:
    def __init__(self):
        self.model = StaffModel()
        self.db = self.model.db
        self.current_staff = "Staff"

    def set_user(self, name):
        self.current_staff = name if name else "Staff"

    MAX_OCCUPANCY = {"Single": 1, "Double": 2, "Queen": 3, "King": 4, "Suite": 6}

    def get_service_staff_list(self):
        return self.model.get_service_staff()

    def calculate_bill(self, bid):
        data = self.model.get_booking_details_for_bill(bid)
        if not data: return None

        try:
            fmt = "%Y-%m-%d"
            start_d = datetime.strptime(data['start_date'], fmt).date()
            today_d = datetime.now().date()
            expected_end = start_d + timedelta(days=data['days'])

            penalty = 0
            penalty_desc = ""

            if today_d < expected_end:
                daily_rate = data['room_cost'] / data['days']
                penalty = daily_rate * 0.5
                penalty_desc = "Early Departure Fee (0.5 Night)"
            elif today_d > expected_end:
                overstay_days = (today_d - expected_end).days
                daily_rate = data['room_cost'] / data['days']
                penalty = daily_rate * overstay_days * 1.5
                penalty_desc = f"Overstay Penalty ({overstay_days} days @ 150%)"

            data['penalty'] = int(penalty)
            data['penalty_desc'] = penalty_desc
            data['final_total'] = data['total'] + int(penalty)
            data['final_balance'] = data['final_total'] - data['paid']
            return data
        except Exception as e:
            print("Calc Error:", e)
            return data

    def get_checkout_cards(self):
        raw_data = self.model.get_checkout_candidates()
        card_list = []
        for r in raw_data:
            financials = self.calculate_bill(r[1])
            if financials:
                financials['room'] = r[0]
                financials['bid'] = r[1]
                card_list.append(financials)
        return card_list

    def process_checkout(self, data, tendered_amount, method):
        try:
            bid = data['bid']
            guest_name = data.get('guest', data.get('name', 'Guest'))

            total_bill = data['final_total']
            paid_prev = data['paid']
            balance = total_bill - paid_prev

            revenue_record = min(tendered_amount, balance) if tendered_amount > 0 else 0

            remark = "Checkout Settlement"
            if data.get('penalty', 0) > 0:
                remark += f" (Inc. {data['penalty_desc']})"

            pay_id = None
            if revenue_record > 0:
                pay_id = self.model.add_payment(bid, guest_name, data['room_cost'], data['svc_cost'],
                                                data['final_total'], method, revenue_record,
                                                self.current_staff, remark, None)

            self.model.update_booking_status(bid, 'Checked Out')
            self.model.update_room_status(data['room'], 'Dirty')
            self.model.add_booking_log(bid, guest_name, 'Checked Out', self.current_staff)

            receipt_data = data.copy()
            receipt_data['guest'] = guest_name
            receipt_data['staff'] = self.current_staff
            receipt_data['paid_prev'] = paid_prev
            receipt_data['remark'] = remark

            try:
                self.generate_receipt(receipt_data, tendered_amount, method, pay_id)
            except Exception as receipt_err:
                print(f"Receipt generation failed (non-critical): {receipt_err}")

            return True, "Checkout Complete"

        except Exception as e:
            print(f"CRITICAL ERROR in process_checkout: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Checkout failed: {str(e)}"

    def generate_receipt(self, data, paid_now, method, payment_id):
        if not payment_id: return

        try:
            now = datetime.now()
            serial_number = f"OR-{now.strftime('%Y%m')}-{payment_id:06d}"

            folder_date = now.strftime("%Y-%m-%d")
            save_dir = os.path.join("receipts", folder_date)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            timestamp = now.strftime("%H%M%S")
            filename = f"{serial_number}_{now.strftime('%Y%m%d')}_{timestamp}.pdf"
            full_path = os.path.abspath(os.path.join(save_dir, filename))

            total   = data.get('final_total', 0)
            prev    = data.get('paid_prev', 0)
            change  = max(0, (prev + paid_now) - total)

            html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: 11pt;
      color: #1a1a1a;
      line-height: 1.35;
      padding: 18px 32px;
  }}
  .header {{
      text-align: center;
      border-bottom: 3px double #222;
      padding-bottom: 8px;
      margin-bottom: 12px;
  }}
  .hotel-name {{
      font-size: 24pt;
      font-weight: 900;
      letter-spacing: 4px;
      color: #B71C1C;
      margin-bottom: 1px;
  }}
  .receipt-title {{
      font-size: 11pt;
      font-weight: bold;
      letter-spacing: 3px;
      color: #333;
      margin-bottom: 2px;
  }}
  .hotel-address {{ font-size: 9pt; color: #666; }}
  .meta-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 12px;
      font-size: 10pt;
  }}
  .meta-table td {{ padding: 2px 6px; border-bottom: 1px solid #eee; vertical-align: top; }}
  .meta-table .lbl {{ font-weight: bold; color: #444; width: 36%; white-space: nowrap; }}
  .meta-table .val {{ color: #111; }}
  .items-table {{ width: 100%; border-collapse: collapse; font-size: 11pt; }}
  .items-table thead tr {{ background-color: #2C3E50; color: white; }}
  .items-table thead th {{ padding: 6px 10px; font-size: 10pt; font-weight: bold; text-align: left; }}
  .items-table thead th:last-child {{ text-align: right; }}
  .items-table tbody td {{ padding: 6px 10px; border-bottom: 1px solid #ddd; }}
  .items-table tbody td:last-child {{ text-align: right; font-weight: bold; }}
  .items-table .divider td {{ border-bottom: 2px solid #333; padding: 1px 0; }}
  .row-grand td {{
      font-size: 13pt; font-weight: 900; background-color: #EEEEEE;
      padding: 7px 10px; border-bottom: 2px solid #333;
  }}
  .row-sub td {{ font-size: 10pt; color: #444; padding: 4px 10px; padding-left: 20px; }}
  .row-tendered td {{
      font-size: 11pt; font-weight: bold; background-color: #FAFAFA;
      padding: 5px 10px; padding-left: 20px; border-bottom: 1px solid #ddd;
  }}
  .row-change td {{
      font-size: 12pt; font-weight: 900; color: #1B5E20;
      background-color: #E8F5E9; padding: 5px 10px; padding-left: 20px;
  }}
  .footer {{
      text-align: center; border-top: 3px double #222;
      margin-top: 14px; padding-top: 8px;
  }}
  .remark    {{ font-size: 9pt;  color: #555; margin-bottom: 4px; }}
  .thankyou  {{ font-size: 12pt; font-weight: bold; color: #B71C1C; margin-bottom: 3px; }}
  .generated {{ font-size: 8pt;  color: #aaa; }}
</style>
</head>
<body>

<div class="header">
  <div class="hotel-name">HOTELLA</div>
  <div class="receipt-title">OFFICIAL RECEIPT</div>
  <div class="hotel-address">Hotella Resort &amp; Hotel &nbsp;|&nbsp; Davao City, Philippines</div>
</div>

<table class="meta-table">
  <tr><td class="lbl">Serial No:</td>      <td class="val">{serial_number}</td></tr>
  <tr><td class="lbl">Date:</td>           <td class="val">{now.strftime('%B %d, %Y   %I:%M %p')}</td></tr>
  <tr><td class="lbl">Booking Ref:</td>    <td class="val">{data.get('bid', 'N/A')}</td></tr>
  <tr><td class="lbl">Guest Name:</td>     <td class="val">{data.get('guest', 'N/A')}</td></tr>
  <tr><td class="lbl">Room Number:</td>    <td class="val">{data.get('room', 'N/A')}</td></tr>
  <tr><td class="lbl">Payment Method:</td> <td class="val">{method}</td></tr>
  <tr><td class="lbl">Processed By:</td>   <td class="val">{data.get('staff', self.current_staff)}</td></tr>
</table>

<table class="items-table">
  <thead>
    <tr><th>Description</th><th>Amount</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Room Charge</td>
      <td>&#8369; {data.get('room_cost', 0):,}</td>
    </tr>
"""
            if data.get('svc_cost', 0) > 0:
                html += f"""
    <tr>
      <td>Services</td>
      <td>&#8369; {data['svc_cost']:,}</td>
    </tr>
"""
            if data.get('penalty', 0) > 0:
                html += f"""
    <tr>
      <td>{data.get('penalty_desc', 'Penalty')}</td>
      <td>&#8369; {data['penalty']:,}</td>
    </tr>
"""
            html += f"""
    <tr class="divider"><td colspan="2"></td></tr>

    <!-- GRAND TOTAL -->
    <tr class="row-grand">
      <td>GRAND TOTAL</td>
      <td>&#8369; {total:,}</td>
    </tr>
    <tr class="row-sub">
      <td>Previously Paid</td>
      <td>&#8369; {prev:,}</td>
    </tr>
    <tr class="row-tendered">
      <td>Amount Tendered</td>
      <td>&#8369; {paid_now:,}</td>
    </tr>
    <tr class="row-change">
      <td>CHANGE</td>
      <td>&#8369; {change:,}</td>
    </tr>
  </tbody>
</table>

<!-- FOOTER -->
<div class="footer">
  <p class="remark">{data.get('remark', 'Payment')}</p>
  <p class="thankyou">Thank you for staying with us!</p>
  <p class="generated">This is a computer-generated receipt.</p>
</div>

</body>
</html>
"""

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(full_path)
            # ✅ A4 gives enough space for large, readable fonts
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)
            print(f"Receipt Saved: {full_path}")

        except Exception as e:
            print(f"PDF GENERATION FAILED (Non-Critical): {e}")

    def add_service_charge(self, bid, room_number, service_name, price, quantity, employee_name):
        emp_data = self.model.get_employee_metadata(employee_name)
        if not emp_data: return False, "Invalid Staff Member"
        emp_id, role = emp_data
        forbidden_roles = ["Manager", "Receptionist", "Cleaner"]
        if role in forbidden_roles: return False, f"Permission Denied: {role}s cannot perform Room Service."
        total = price * quantity
        date = datetime.now().strftime("%Y-%m-%d")
        if self.model.add_service(bid, room_number, service_name, total, date, emp_id, quantity):
            return True, "Service Added Successfully"
        return False, "Database Error"

    def get_active_room_details(self, room_number):
        return self.model.get_active_guest(room_number)

    def get_stats(self):
        return self.model.get_room_counts()

    def get_map_data(self):
        return self.model.get_all_rooms_data()

    def search_rooms(self, d_in, d_out):
        return self.model.get_available_rooms(d_in, d_out)

    def get_room_prices(self):
        return {"Single": 1500, "Double": 2500, "Queen": 3500, "King": 4500, "Suite": 6000}

    def get_todays_arrivals(self):
        return self.model.get_todays_bookings()

    def cancel_booking_today(self, bid, name):
        if self.model.update_booking_status(bid, 'Cancelled'):
            self.model.add_booking_log(bid, name, "Cancelled", self.current_staff)
            return True, "Booking Cancelled"
        return False, "Error"

    def create_booking_final(self, data, room_id, payment_data):
        selected_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        if selected_date < datetime.now().date():
            return False, "You cannot book for a past date."
        total    = data['total_price']
        paid     = payment_data['amount']
        method   = payment_data['method']
        card_num = payment_data.get('card_number', None)
        guests   = data.get('guests', 1)
        room_type = data.get('room_type')
        limit = self.MAX_OCCUPANCY.get(room_type, 2)
        if guests > limit:
            return False, f"Maximum occupancy for {room_type} is {limit} guest(s)."
        if "Credit Card" not in method:
            min_req = int(total * 0.20)
            if paid < min_req:
                return False, f"Minimum 20% downpayment (₱{min_req:,}) is required."
        bid = self.model.create_booking_final(data, room_id, self.current_staff)
        if bid:
            guest_name  = data.get('name') or data.get('Name', 'Guest')
            remark_text = "Downpayment"
            pay_id = self.model.add_payment(bid, guest_name, total, 0, total, method, paid,
                                            self.current_staff, remark_text, card_num)
            if pay_id and paid > 0:
                receipt_data = {
                    'bid': bid, 'guest': guest_name, 'room': room_id,
                    'type': data.get('room_type'), 'staff': self.current_staff,
                    'room_cost': total, 'svc_cost': 0, 'final_total': total,
                    'paid_prev': 0, 'remark': remark_text, 'penalty': 0, 'penalty_desc': ''
                }
                self.generate_receipt(receipt_data, paid, method, pay_id)
            self.model.add_booking_log(bid, guest_name, "Booking Created", self.current_staff)
            return True, bid
        return False, "Database Error"

    def get_available_cleaners(self):
        return self.model.get_available_cleaners()

    def assign_cleaner(self, room_num, emp_name):
        cleaners = self.model.get_available_cleaners()
        emp_id = next((c[0] for c in cleaners if c[1] == emp_name), None)
        if emp_id and self.model.assign_cleaner_to_room(room_num, emp_id):
            return True, "Cleaner assigned!"
        return False, "Failed"

    def finish_cleaning(self, room_num):
        return (True, "Room Clean") if self.model.finish_cleaning_room(room_num) else (False, "Failed")

    def mark_arrived(self, bid, name):
        room_data = self.model.get_room_status_by_booking(bid)
        if room_data and room_data[0] in ['Dirty', 'Cleaning']:
            return False, f"Room {room_data[1]} is {room_data[0]}."
        if self.model.update_booking_status(bid, "Checked In"):
            self.model.add_booking_log(bid, name, "Checked In", self.current_staff)
            if room_data:
                self.model.update_room_status(room_data[1], 'Occupied')
            return True, "Guest Checked In"
        return False, "Error"

    def get_all_bookings(self):
        return self.model.get_all_bookings()

    def get_overdue_guests(self):
        active_bookings = self.model.get_all_bookings()
        overdue_list = []
        today = datetime.now().date()
        for b in active_bookings:
            if b.get('status') == 'Checked In':
                try:
                    date_str = str(b.get('date', ''))
                    days = b.get('days')
                    if not date_str or days is None: continue
                    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    expected_checkout = start_date + timedelta(days=int(days))
                    if today > expected_checkout:
                        days_over = (today - expected_checkout).days
                        b['overdue_by'] = days_over
                        overdue_list.append(b)
                except:
                    continue
        return overdue_list