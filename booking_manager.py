import sqlite3
from objects import *
from auth import *


class BookingManager:
    def __init__(self, connection):
        self.conn = connection
        self.c = connection.cursor()

    def get_teacher_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, subject, password, schedule
            FROM teachers
            WHERE email = ?
        """, (email,)).fetchone()
        if not row:
            return None
        name, email, subject, password, schedule_str = row
        teacher_obj = teacher(name, email, subject, password)
        teacher_obj.schedule = string_to_list(schedule_str)
        return teacher_obj

    def get_student_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, password, schedule
            FROM students
            WHERE email = ?
        """, (email,)).fetchone()
        if not row:
            return None
        name, email, password, schedule_str = row
        student_obj = student(name, email, password)
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

    def update_teacher_schedule(self, teacher):
        schedule_str = list_to_string(teacher.schedule)
        self.c.execute("UPDATE teachers SET schedule=? WHERE email=?",
                       (schedule_str, teacher.email))
        self.conn.commit()

    def update_student_schedule(self, student):
        schedule_str = list_to_string(student.schedule)
        self.c.execute("UPDATE students SET schedule=? WHERE email=?",
                       (schedule_str, student.email))
        self.conn.commit()

    def save_booking(self, teacher_email, student_email, day, hour):
        self.c.execute("""
            INSERT INTO bookings (teacher_email, student_email, day, hour)
            VALUES (?, ?, ?, ?)
        """, (teacher_email, student_email, day, hour))
        self.conn.commit()

    def remove_booking(self, teacher_email, student_email, day, hour):
        self.c.execute("""
            DELETE FROM bookings
            WHERE teacher_email = ? AND student_email = ?
            AND day = ? AND hour = ?
        """, (teacher_email, student_email, day, hour))
        self.conn.commit()

    def book(self, teacher, student, day, hour):
        """Books a lesson for both teacher + student."""
        if not self.is_available(teacher, student, day, hour):
            return False
        teacher.schedule[day][hour] = False
        student.schedule[day][hour] = False
        self.update_teacher_schedule(teacher)
        self.update_student_schedule(student)
        self.save_booking(teacher.email, student.email, day, hour)

        return True

    def cancel(self, teacher, student, day, hour):
        """Cancel student + teacher booking."""
        teacher.schedule[day][hour] = True
        student.schedule[day][hour] = True
        self.update_teacher_schedule(teacher)
        self.update_student_schedule(student)
        self.remove_booking(teacher.email, student.email, day, hour)

    def get_bookings_for_teacher(self, teacher_email):
        rows = self.c.execute("""
            SELECT student_email, day, hour
            FROM bookings
            WHERE teacher_email = ?
            ORDER BY day, hour
        """, (teacher_email,)).fetchall()

        return [
            {"student_email": row[0], "day": row[1], "hour": row[2]}
            for row in rows
        ]

    def get_bookings_for_student(self, student_email):
        rows = self.c.execute("""
            SELECT teacher_email, day, hour
            FROM bookings
            WHERE student_email = ?
            ORDER BY day, hour
        """, (student_email,)).fetchall()

        return [
            {"teacher_email": row[0], "day": row[1], "hour": row[2]}
            for row in rows
        ]

    def register_teacher(self, name, email, subject, password):
        if self.get_teacher_by_email(email):
            return False
        hashed = hash_password(password)
        schedule_str = list_to_string([[True] * 13 for _ in range(6)])
        self.c.execute("""
            INSERT INTO teachers (name, email, subject, password, schedule)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, subject, hashed, schedule_str))
        self.conn.commit()
        return True

    def register_student(self, name, email, password):
        if self.get_student_by_email(email):
            return False

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
            return None
        name, email, subject, stored_hash, schedule = row
        if not verify_password(password, stored_hash):
            return False
        teacher_object = teacher(name, email, subject, stored_hash)
        teacher_object.schedule = string_to_list(schedule)
        return teacher_object

    def login_student(self, email, password):
        row = self.c.execute("""
                SELECT name, email, password, schedule
                FROM students
                WHERE email = ?
            """, (email,)).fetchone()
        if not row:
            return None
        name, email, stored_hash, schedule = row
        if not verify_password(password, stored_hash):
            return False
        student_object = student(name, email, stored_hash)
        student_object.schedule = string_to_list(schedule)
        return student_object
