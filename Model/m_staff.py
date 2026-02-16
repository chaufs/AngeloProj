from Model.m_database import Database
from datetime import datetime


class StaffModel:
    def __init__(self):
        self.db = Database()

    # 🟢 NEW: Fetch only employees allowed to do Room Service
    def get_service_staff(self):
        c = self.db.get_cursor()
        try:
            c.execute(
                "SELECT name FROM employees WHERE role IN ('Room Service', 'Waiter', 'Kitchen') AND status='Active'")
            return [r[0] for r in c.fetchall()]
        finally:
            c.close()

    # 🟢 NEW: Get details for Bill Calculation (Start Date, Price, etc.)
    def get_booking_details_for_bill(self, bid):
        c = self.db.get_cursor()
        try:
            bid_int = int(bid.replace("B", ""))
            # Fetch start date and duration to calculate penalties
            c.execute("SELECT name, price, room_type, date, days FROM bookings WHERE id=%s", (bid_int,))
            b = c.fetchone()
            if not b: return None

            name, price, rtype, start_date_str, duration = b

            c.execute("SELECT SUM(price) FROM services WHERE booking_id=%s", (bid,))
            svc = c.fetchone()[0] or 0

            c.execute("SELECT SUM(amount_paid) FROM payments WHERE booking_id=%s", (bid,))
            paid = c.fetchone()[0] or 0

            return {
                'guest': name,
                'type': rtype,
                'room_cost': price,
                'svc_cost': svc,
                'total': price + svc,
                'paid': paid,
                'start_date': start_date_str,
                'days': duration
            }
        except:
            return None
        finally:
            c.close()

    # --- EXISTING METHODS ---
    def get_available_cleaners(self):
        c = self.db.get_cursor()
        try:
            c.execute("SELECT id, name FROM employees WHERE role='Cleaner' AND status='Active'")
            return c.fetchall()
        finally:
            c.close()

    def assign_cleaner_to_room(self, room_num, emp_id):
        c = self.db.get_cursor()
        try:
            c.execute("UPDATE rooms SET status='Cleaning', assigned_employee_id=%s WHERE room_number=%s",
                      (emp_id, room_num))
            c.execute("UPDATE employees SET status='Busy' WHERE id=%s", (emp_id,))
            self.db.conn.commit();
            return True
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def finish_cleaning_room(self, room_num):
        c = self.db.get_cursor()
        try:
            c.execute("SELECT assigned_employee_id FROM rooms WHERE room_number=%s", (room_num,))
            emp_id = c.fetchone()
            emp_id = emp_id[0] if emp_id else None
            c.execute("UPDATE rooms SET status='Vacant', assigned_employee_id=NULL WHERE room_number=%s", (room_num,))
            if emp_id: c.execute("UPDATE employees SET status='Active' WHERE id=%s", (emp_id,))
            self.db.conn.commit();
            return True
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def get_room_status_by_booking(self, bid):
        c = self.db.get_cursor();
        c.execute(
            "SELECT r.status, r.room_number FROM transactions t JOIN rooms r ON t.room_number = r.room_number WHERE t.booking_id = %s",
            (bid,));
        return c.fetchone()

    def get_available_rooms(self, d_in, d_out):
        c = self.db.get_cursor()
        try:
            sql = """SELECT room_number, description, status FROM rooms WHERE room_number NOT IN (
                SELECT t.room_number FROM transactions t JOIN bookings b ON t.booking_id = CONCAT('B', LPAD(b.id, 5, '0'))
                WHERE b.status != 'Cancelled' AND NOT (DATE_ADD(STR_TO_DATE(b.date, '%Y-%m-%d'), INTERVAL b.days DAY) <= %s OR STR_TO_DATE(b.date, '%Y-%m-%d') >= %s)
            ) AND status != 'Maintenance' ORDER BY room_number"""
            c.execute(sql, (d_in, d_out));
            return c.fetchall()
        except:
            return []
        finally:
            c.close()

    def get_checkout_candidates(self):
        c = self.db.get_cursor()
        try:
            sql = """SELECT t.room_number, t.booking_id, b.price, b.name FROM transactions t JOIN bookings b ON t.booking_id = CONCAT('B', LPAD(b.id, 5, '0')) JOIN rooms r ON t.room_number = r.room_number WHERE r.status='Occupied' AND b.status IN ('Confirmed', 'Arrived', 'Checked In')"""
            c.execute(sql);
            return c.fetchall()
        except:
            return []
        finally:
            c.close()

    def get_room_counts(self):
        c = self.db.get_cursor()
        try:
            c.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'")
            total = c.fetchone()[0]
            c.execute("SELECT status, COUNT(*) FROM rooms GROUP BY status")
            stats = dict(c.fetchall())
            return total, stats.get('Vacant', 0), stats.get('Occupied', 0), stats.get('Dirty', 0)
        finally:
            c.close()

    def get_all_rooms_data(self):
        c = self.db.get_cursor(); c.execute(
            "SELECT room_number, status, description, assigned_employee_id FROM rooms"); return c.fetchall()

    def create_booking_final(self, d, room_id, staff_name):
        c = self.db.get_cursor()
        try:
            name = d.get('name') or d.get('Name', '')
            sql = "INSERT INTO bookings (name, email, phone, address, room_type, date, days, price, status, guests_count, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', %s, %s)"
            vals = (name, d.get('email'), d.get('phone'), d.get('address'), d['room_type'], d['date'], d['days'],
                    d['total_price'], d['guests'], staff_name)
            c.execute(sql, vals)
            c.execute("SELECT LAST_INSERT_ID()")
            bid = f"B{c.fetchone()[0]:05d}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO transactions (booking_id, room_number, date_confirmed) VALUES (%s, %s, %s)",
                      (bid, room_id, now))
            self.db.conn.commit();
            return bid
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def add_payment(self, bid, name, r, s, g, m, a, staff_name, remarks, card_num=None):
        c = self.db.get_cursor()
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            sql = "INSERT INTO payments (booking_id, customer_name, room_total, service_total, grand_total, method, date_paid, amount_paid, card_number, processed_by, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            c.execute(sql, (bid, name, r, s, g, m, date, a, card_num, staff_name, remarks))

            # 🔴 NEW: Get the ID of the payment we just inserted
            c.execute("SELECT LAST_INSERT_ID()")
            payment_id = c.fetchone()[0]

            self.db.conn.commit()
            return payment_id  # Return ID instead of True
        except:
            self.db.conn.rollback()
            return None
        finally:
            c.close()

    def get_active_guest(self, room_num):
        c = self.db.get_cursor()
        try:
            sql = "SELECT b.id, b.name FROM transactions t JOIN bookings b ON t.booking_id = CONCAT('B', LPAD(b.id, 5, '0')) JOIN rooms r ON t.room_number = r.room_number WHERE r.room_number = %s AND r.status = 'Occupied' AND b.status IN ('Confirmed', 'Arrived', 'Checked In') ORDER BY b.id DESC LIMIT 1"
            c.execute(sql, (room_num,));
            row = c.fetchone()
            return (f"B{row[0]:05d}", row[1]) if row else (None, None)
        finally:
            c.close()

    def add_service(self, bid, room, name, total_cost, date, emp_id, quantity):
        c = self.db.get_cursor()
        try:
            c.execute(
                "INSERT INTO services (booking_id, room_number, service_name, price, date, employee_id, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (bid, room, name, total_cost, date, emp_id, quantity))
            self.db.conn.commit();
            return True
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def get_todays_bookings(self):
        c = self.db.get_cursor()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute(
                "SELECT b.id, b.name, b.room_type, t.room_number, b.price, b.status FROM bookings b LEFT JOIN transactions t ON t.booking_id = CONCAT('B', LPAD(b.id, 5, '0')) WHERE b.date = %s AND b.status IN ('Confirmed', 'Checked In', 'Arrived')",
                (today,))
            rows = c.fetchall()
            return [{'bid': f"B{r[0]:05d}", 'name': r[1], 'type': r[2], 'room': r[3], 'price': r[4], 'status': r[5]} for
                    r in rows]
        except:
            return []
        finally:
            c.close()

    def update_booking_status(self, bid, new_status):
        c = self.db.get_cursor()
        try:
            bid_int = int(bid.replace("B", ""))
            c.execute("UPDATE bookings SET status=%s WHERE id=%s", (new_status, bid_int))
            if new_status == 'Cancelled':
                c.execute("SELECT room_number FROM transactions WHERE booking_id=%s", (bid,))
                res = c.fetchone()
                if res: c.execute("UPDATE rooms SET status='Vacant' WHERE room_number=%s", (res[0],))
            self.db.conn.commit();
            return True
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def add_booking_log(self, bid, guest, action, staff_name="---"):
        c = self.db.get_cursor()
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "INSERT INTO booking_logs (booking_id, guest_name, action_type, timestamp, performed_by) VALUES (%s, %s, %s, %s, %s)",
                (bid, guest, action, now, staff_name))
            self.db.conn.commit();
            return True
        except:
            self.db.conn.rollback(); return False
        finally:
            c.close()

    def get_all_bookings(self):
        c = self.db.get_cursor(); c.execute(
            "SELECT b.id, b.name, b.room_type, t.room_number, b.price, b.status, b.date, b.days FROM bookings b LEFT JOIN transactions t ON t.booking_id = CONCAT('B', LPAD(b.id, 5, '0')) ORDER BY b.date DESC"); rows = c.fetchall(); return [
            {'bid': f"B{r[0]:05d}", 'name': r[1], 'room_type': r[2], 'room': r[3] or 'N/A', 'price': r[4],
             'status': r[5], 'date': r[6], 'days': r[7]} for r in rows]

    def get_dirty_rooms(self):
        c = self.db.get_cursor(); c.execute(
            "SELECT room_number, description, status FROM rooms WHERE status IN ('Dirty','Housekeeping')"); return c.fetchall()

    def update_room_status(self, r, s):
        c = self.db.get_cursor(); c.execute("UPDATE rooms SET status=%s WHERE room_number=%s",
                                            (s, r)); self.db.conn.commit()

        # 🔴 UPDATED: Fetch ID AND Role for validation
    def get_employee_metadata(self, name):
            c = self.db.get_cursor()
            try:
                c.execute("SELECT id, role FROM employees WHERE name=%s", (name,))
                return c.fetchone()  # Returns (id, role) or None
            finally:
                c.close()