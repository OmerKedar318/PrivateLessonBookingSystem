from auth import *
from exceptions import *
from objects import *


def valid_slot(day, hour):
    return 0 <= day <= 5 and 0 <= hour <= 12


class BookingManager:
    def __init__(self, db_path="database.db"):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def get_teacher_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, subject, password, schedule
            FROM teachers
            WHERE email = ?
        """, (email,)).fetchone()
        if not row:
            raise UserNotFoundError("Teacher not found")
        name, email, subject, password, schedule_str = row
        teacher_obj = Teacher(name, email, subject, password)
        teacher_obj.schedule = string_to_list(schedule_str)
        return teacher_obj

    def get_student_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, password, schedule
            FROM students
            WHERE email = ?
        """, (email,)).fetchone()
        if not row:
            raise UserNotFoundError("Student not found")
        name, email, password, schedule_str = row
        student_obj = Student(name, email, password)
        student_obj.schedule = string_to_list(schedule_str)
        return student_obj

    @staticmethod
    def is_available(teacher, student, day, hour):
        return teacher.schedule[day][hour] and student.schedule[day][hour]

    def find_available_slots(self, teacher, student):
        slots = []
        for d in range(6):
            for h in range(13):
                if self.is_available(teacher, student, d, h):
                    slots.append((d, h))
        return slots

    def get_available_teachers(self, subject, day, hour, student):
        rows = self.c.execute("""
            SELECT name, email, subject, password, schedule
            FROM teachers
            WHERE subject = ?
        """, (subject,)).fetchall()
        available = []
        for name, email, subject, password, schedule_str in rows:
            schedule = string_to_list(schedule_str)
            if not schedule[day][hour]:
                continue
            if student and not student.is_available(day, hour):
                continue
            teacher_obj = Teacher(
                name=name,
                email=email,
                subject=subject,
                password=password
            )
            teacher_obj.schedule = schedule
            available.append(teacher_obj)
        return available

    def update_teacher_schedule(self, teacher):
        schedule_str = list_to_string(teacher.schedule)
        self.c.execute("UPDATE teachers SET schedule=? WHERE email=?",
                       (schedule_str, teacher.email))

    def update_student_schedule(self, student):
        schedule_str = list_to_string(student.schedule)
        self.c.execute("UPDATE students SET schedule=? WHERE email=?",
                       (schedule_str, student.email))

    def save_booking(self, teacher, student, day, hour):
        try:
            self.c.execute("""
                INSERT INTO bookings (teacher_email, student_email, day, hour)
                VALUES (?, ?, ?, ?)
            """, (teacher.email, student.email, day, hour))
            return c.lastrowid
        except sqlite3.IntegrityError:
            raise SlotUnavailableError("Slot already booked")

    def remove_booking(self, teacher, student, day, hour):
        self.c.execute("""
            DELETE FROM bookings
            WHERE teacher_email = ? AND student_email = ?
            AND day = ? AND hour = ?
        """, (teacher.email, student.email, day, hour))

    def book(self, teacher, student, day, hour):
        """Books a lesson for both teacher + student."""
        if not valid_slot(day, hour):
            raise InvalidTimeError("Invalid time slot")
        if not teacher or not student:
            raise UserNotFoundError("Teacher or student not found")
        if not teacher.is_available(day, hour):
            raise SlotUnavailableError("Teacher is busy")
        if not student.is_available(day, hour):
            raise SlotUnavailableError("Student is busy")
        try:
            self.conn.execute("BEGIN")
            teacher.schedule[day][hour] = False
            student.schedule[day][hour] = False
            self.update_teacher_schedule(teacher)
            self.update_student_schedule(student)
            booking_id = self.save_booking(teacher, student, day, hour)
            conn.commit()
            return booking_id
        except Exception as e:
            self.conn.rollback()
            raise BookingError(f"Booking failed: {e}")

    def cancel(self, teacher, student, day, hour):
        """Cancel student + teacher booking."""
        if not valid_slot(day, hour):
            raise InvalidTimeError("Invalid time slot")
        if not teacher or not student:
            raise UserNotFoundError("Teacher or student not found")
        try:
            with self.conn:
                teacher.empty(day, hour)
                student.empty(day, hour)
                self.update_teacher_schedule(teacher)
                self.update_student_schedule(student)
                self.remove_booking(teacher, student, day, hour)
        except Exception as e:
            raise BookingError(f"Cancel failed: {e}")

    def get_bookings_for_teacher(self, teacher):
        rows = self.c.execute("""
            SELECT student_email, day, hour
            FROM bookings
            WHERE teacher_email = ?
            ORDER BY day, hour
        """, (teacher.email,)).fetchall()
        if not rows:
            return []

        return [
            {"student_email": row[0], "day": row[1], "hour": row[2]}
            for row in rows
        ]

    def get_bookings_for_student(self, student):
        rows = self.c.execute("""
            SELECT teacher_email, day, hour
            FROM bookings
            WHERE student_email = ?
            ORDER BY day, hour
        """, (student.email,)).fetchall()
        if not rows:
            return []

        return [
            {"teacher_email": row[0], "day": row[1], "hour": row[2]}
            for row in rows
        ]

    def register_teacher(self, name, email, subject, password):
        try:
            self.get_teacher_by_email(email)
            raise BookingError("Email already exists")
        except UserNotFoundError:
            hashed = hash_password(password)
            schedule_str = list_to_string([[True] * 13 for _ in range(6)])
            self.c.execute("""
                INSERT INTO teachers (name, email, subject, password, schedule)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, subject, hashed, schedule_str))
            self.conn.commit()
            return True

    def register_student(self, name, email, password):
        try:
            self.get_student_by_email(email)
            raise BookingError("Email already exists")
        except UserNotFoundError:
            hashed = hash_password(password)
            schedule_str = list_to_string([[True] * 13 for _ in range(6)])
            self.c.execute("""
                INSERT INTO students (name, email, password, schedule)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed, schedule_str))
            self.conn.commit()
            return True

    def login_teacher(self, email, password):
        row = self.c.execute("""
                SELECT name, email, subject, password, schedule
                FROM teachers
                WHERE email = ?
            """, (email,)).fetchone()
        if not row:
            raise UserNotFoundError("Student not found")
        name, email, subject, stored_hash, schedule = row
        if not verify_password(password, stored_hash):
            raise AuthenticationError("Incorrect password")
        teacher_object = Teacher(name, email, subject, stored_hash)
        teacher_object.schedule = string_to_list(schedule)
        return teacher_object

    def login_student(self, email, password):
        row = self.c.execute("""
                SELECT name, email, password, schedule
                FROM students
                WHERE email = ?
            """, (email,)).fetchone()
        if not row:
            raise UserNotFoundError("Student not found")
        name, email, stored_hash, schedule = row
        if not verify_password(password, stored_hash):
            raise AuthenticationError("Incorrect password")
        student_object = Student(name, email, stored_hash)
        student_object.schedule = string_to_list(schedule)
        return student_object
