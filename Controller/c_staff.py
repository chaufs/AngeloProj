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
            # 🟢 Get guest name safely (handles both 'guest' and 'name' keys)
            guest_name = data.get('guest', data.get('name', 'Guest'))

            # Calculate totals
            total_bill = data['final_total']
            paid_prev = data['paid']
            balance = total_bill - paid_prev

            # Only record revenue for the amount they actually owe
            revenue_record = min(tendered_amount, balance) if tendered_amount > 0 else 0

            remark = "Checkout Settlement"
            if data.get('penalty', 0) > 0:
                remark += f" (Inc. {data['penalty_desc']})"

            # 1. Add Payment to DB
            pay_id = None
            if revenue_record > 0:
                # 🔴 FIX: Use 'guest_name' variable instead of data['name']
                pay_id = self.model.add_payment(bid, guest_name, data['room_cost'], data['svc_cost'],
                                                data['final_total'], method, revenue_record,
                                                self.current_staff, remark, None)

            # 2. Update Statuses
            self.model.update_booking_status(bid, 'Checked Out')
            self.model.update_room_status(data['room'], 'Dirty')
            # 🔴 FIX: Use 'guest_name' here too
            self.model.add_booking_log(bid, guest_name, 'Checked Out', self.current_staff)

            # 3. Generate Receipt (Safe Call)
            receipt_data = data.copy()
            receipt_data['guest'] = guest_name
            receipt_data['staff'] = self.current_staff
            receipt_data['paid_prev'] = paid_prev
            receipt_data['remark'] = remark

            # Try to generate receipt, but don't fail checkout if it errors
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

    # 🔴 FIX: CRASH FIX - Removed setPageMargins call
    def generate_receipt(self, data, paid_now, method, payment_id):
        if not payment_id: return

        try:
            now = datetime.now()
            serial_number = f"OR-{now.strftime('%Y%m')}-{payment_id:06d}"

            folder_date = now.strftime("%Y-%m-%d")
            save_dir = os.path.join("receipts", folder_date)
            if not os.path.exists(save_dir): os.makedirs(save_dir)

            timestamp = now.strftime("%H%M%S")
            filename = f"{serial_number}_{now.strftime('%Y%m%d')}_{timestamp}.pdf"
            full_path = os.path.abspath(os.path.join(save_dir, filename))

            total = data.get('final_total', 0)
            prev = data.get('paid_prev', 0)
            change = max(0, (prev + paid_now) - total)

            # Improved receipt with better readability
            html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: 'Arial', 'Helvetica', sans-serif; 
                        font-size: 14px; 
                        margin: 40px; 
                        line-height: 1.6;
                    }}
                    .header {{ 
                        text-align: center; 
                        border-bottom: 3px double black; 
                        padding-bottom: 15px; 
                        margin-bottom: 20px;
                    }}
                    .header h1 {{
                        font-size: 24px;
                        font-weight: bold;
                        margin: 5px 0;
                        letter-spacing: 1px;
                    }}
                    .header p {{
                        font-size: 13px;
                        margin: 3px 0;
                        color: #333;
                    }}
                    .meta {{ 
                        font-size: 13px; 
                        margin: 20px 0;
                        line-height: 1.8;
                    }}
                    .meta b {{
                        font-size: 14px;
                    }}
                    table {{ 
                        width: 100%; 
                        margin-top: 25px; 
                        border-collapse: collapse; 
                        font-size: 14px;
                    }}
                    td {{ 
                        padding: 10px 8px;
                        border-bottom: 1px solid #ddd;
                    }}
                    .desc-col {{ 
                        width: 65%; 
                        font-weight: 500;
                    }}
                    .amount-col {{ 
                        width: 35%; 
                        text-align: right; 
                        font-weight: 500;
                    }}
                    .right {{ text-align: right; }}
                    .line {{ 
                        border-bottom: 2px solid #333; 
                    }}
                    .total-row {{
                        font-size: 16px;
                        font-weight: bold;
                        background-color: #f5f5f5;
                    }}
                    .footer {{ 
                        text-align: center; 
                        font-size: 12px; 
                        margin-top: 30px; 
                        padding-top: 20px;
                        border-top: 2px dashed #999;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>HOTELLA</h1>
                    <h2 style="margin: 5px 0; font-size: 18px; font-weight: 600;">OFFICIAL RECEIPT</h2>
                    <p>Hotella Resort & Hotel</p>
                    <p>Davao City, Philippines</p>
                </div>

                <div class="meta">
                    <b>SERIAL NO:</b> {serial_number}<br>
                    <b>Date:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <b>Booking Ref:</b> {data.get('bid', 'N/A')}<br>
                    <b>Guest Name:</b> {data.get('guest', 'Guest')}<br>
                    <b>Room Number:</b> {data.get('room', 'N/A')}<br>
                    <b>Processed By:</b> {data.get('staff', 'Staff')}
                </div>

                <table>
                    <tr style="border-bottom: 2px solid #333;">
                        <td class="desc-col" style="font-weight: bold; font-size: 15px;">Description</td>
                        <td class="amount-col" style="font-weight: bold; font-size: 15px;">Amount</td>
                    </tr>
                    <tr>
                        <td class="desc-col">Room Charge</td>
                        <td class="amount-col">₱ {data.get('room_cost', 0):,}</td>
                    </tr>
            """

            if data.get('svc_cost', 0) > 0:
                html += f"""
                    <tr>
                        <td class="desc-col">Services</td>
                        <td class="amount-col">₱ {data['svc_cost']:,}</td>
                    </tr>
                """

            if data.get('penalty', 0) > 0:
                html += f"""
                    <tr>
                        <td class="desc-col">{data.get('penalty_desc', 'Penalty')}</td>
                        <td class="amount-col">₱ {data['penalty']:,}</td>
                    </tr>
                """

            html += f"""
                    <tr class="line">
                        <td colspan="2"></td>
                    </tr>
                    <tr class="total-row">
                        <td class="desc-col">GRAND TOTAL</td>
                        <td class="amount-col">₱ {total:,}</td>
                    </tr>
                    <tr>
                        <td class="desc-col" style="padding-left: 20px;">Previously Paid</td>
                        <td class="amount-col">₱ {prev:,}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td class="desc-col" style="padding-left: 20px;"><b>Amount Tendered</b></td>
                        <td class="amount-col"><b>₱ {paid_now:,}</b></td>
                    </tr>
                    <tr style="background-color: #e8f5e9;">
                        <td class="desc-col" style="padding-left: 20px;"><b>CHANGE</b></td>
                        <td class="amount-col"><b>₱ {change:,}</b></td>
                    </tr>
                </table>

                <div class="footer">
                    <p style="margin: 5px 0; font-size: 13px;"><b>{data.get('remark', 'Payment')}</b></p>
                    <p style="margin: 15px 0 5px 0; font-size: 14px; font-weight: 600;">Thank you for staying with us!</p>
                    <p style="margin: 5px 0;">This is a computer-generated receipt.</p>
                </div>
            </body>
            </html>
            """

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(full_path)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A5))  # 🟢 CHANGED: A6 → A5 for larger receipt

            # ⛔ CRITICAL FIX: DO NOT ADD SETPAGEMARGINS HERE. IT WILL CRASH.

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
            self.model.add_booking_log(bid, name, "Cancelled", self.current_staff);
            return True, "Booking Cancelled"
        return False, "Error"

    def create_booking_final(self, data, room_id, payment_data):
        selected_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        if selected_date < datetime.now().date(): return False, "You cannot book for a past date."
        total = data['total_price'];
        paid = payment_data['amount'];
        method = payment_data['method'];
        card_num = payment_data.get('card_number', None)
        guests = data.get('guests', 1);
        room_type = data.get('room_type');
        limit = self.MAX_OCCUPANCY.get(room_type, 2)
        if guests > limit: return False, f"Maximum occupancy for {room_type} is {limit} guest(s)."
        if "Credit Card" not in method:
            min_req = int(total * 0.20)
            if paid < min_req: return False, f"Minimum 20% downpayment (₱{min_req:,}) is required."
        bid = self.model.create_booking_final(data, room_id, self.current_staff)
        if bid:
            guest_name = data.get('name') or data.get('Name', 'Guest');
            remark_text = "Downpayment"
            pay_id = self.model.add_payment(bid, guest_name, total, 0, total, method, paid, self.current_staff,
                                            remark_text, card_num)
            if pay_id and paid > 0:
                receipt_data = {'bid': bid, 'guest': guest_name, 'room': room_id, 'type': data.get('room_type'),
                                'staff': self.current_staff, 'room_cost': total, 'svc_cost': 0, 'final_total': total,
                                'paid_prev': 0, 'remark': remark_text}
                self.generate_receipt(receipt_data, paid, method, pay_id)
            self.model.add_booking_log(bid, guest_name, "Booking Created", self.current_staff);
            return True, bid
        return False, "Database Error"

    def get_available_cleaners(self):
        return self.model.get_available_cleaners()

    def assign_cleaner(self, room_num, emp_name):
        cleaners = self.model.get_available_cleaners();
        emp_id = next((c[0] for c in cleaners if c[1] == emp_name), None)
        if emp_id and self.model.assign_cleaner_to_room(room_num, emp_id): return True, "Cleaner assigned!"
        return False, "Failed"

    def finish_cleaning(self, room_num):
        return (True, "Room Clean") if self.model.finish_cleaning_room(room_num) else (False, "Failed")

    def mark_arrived(self, bid, name):
        room_data = self.model.get_room_status_by_booking(bid)
        if room_data and room_data[0] in ['Dirty', 'Cleaning']: return False, f"Room {room_data[1]} is {room_data[0]}."
        if self.model.update_booking_status(bid, "Checked In"):
            self.model.add_booking_log(bid, name, "Checked In", self.current_staff)
            if room_data: self.model.update_room_status(room_data[1], 'Occupied')
            return True, "Guest Checked In"
        return False, "Error"

    def get_all_bookings(self):
        return self.model.get_all_bookings()

    def get_overdue_guests(self):
        active_bookings = self.model.get_all_bookings();
        overdue_list = [];
        today = datetime.now().date()
        for b in active_bookings:
            if b.get('status') == 'Checked In':
                try:
                    date_str = str(b.get('date', ''));
                    days = b.get('days')
                    if not date_str or days is None: continue
                    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    expected_checkout = start_date + timedelta(days=int(days))
                    if today > expected_checkout:
                        days_over = (today - expected_checkout).days;
                        b['overdue_by'] = days_over;
                        overdue_list.append(b)
                except:
                    continue
        return overdue_list