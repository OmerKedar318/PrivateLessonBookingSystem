import sqlite3
from auth import hash_password


def list_to_string(two_d_list):
    """Convert a 2D boolean list to a simple string."""
    return "\n".join(",".join("1" if val else "0" for val in row)
                     for row in two_d_list)


def string_to_list(s):
    """Convert the string back into a 2D boolean list."""
    return [
        [True if x == "1" else False for x in line.split(",")]
        for line in s.split("\n")
    ]


conn = sqlite3.connect('database.db')
c = conn.cursor()


class teacher:
    def __init__(self, name, email, subject, password):
        self.name = name
        self.email = email
        self.subject = subject
        self.password = password
        self.schedule = [[True] * 13 for _ in range(6)]

    def save_new_teacher(self):
        # Check if teacher already exists by email
        result = c.execute("SELECT email FROM teachers WHERE email=?",
                           (self.email,)).fetchone()

        if not result:
            schedule_str = list_to_string(self.schedule)
            c.execute("""
                INSERT INTO teachers (name, email, subject, password, schedule)
                VALUES (?, ?, ?, ?, ?)
            """, (self.name, self.email, self.subject, self.password, schedule_str))
            conn.commit()
        else:
            # If exists, load schedule from DB
            self.load_schedule()

    def save_schedule(self):
        schedule_str = list_to_string(self.schedule)
        c.execute("UPDATE teachers SET schedule = ? WHERE email = ?",
                  (schedule_str, self.email))
        conn.commit()

    def load_schedule(self):
        row = c.execute(
            "SELECT schedule FROM teachers WHERE email=?",
            (self.email,)
        ).fetchone()
        if row:
            self.schedule = string_to_list(row[0])

    def fill(self, day, hour):
        self.schedule[day][hour] = False
        self.save_schedule()

    def empty(self, day, hour):
        self.schedule[day][hour] = True
        self.save_schedule()

    def is_available(self, day, hour):
        return self.schedule[day][hour]

    def get_available_slots(self):
        slots = []
        for d in range(6):
            for h in range(13):
                if self.schedule[d][h]:
                    slots.append((d, h))
        return slots

    def print_schedule(self):
        print(f"Schedule for {self.name}:")
        for day in self.schedule:
            print(" ".join("T" if x else "F" for x in day))

    def update_email(self, new_email):
        c.execute("UPDATE teachers SET email=? WHERE email=?",
                  (new_email, self.email))
        conn.commit()
        self.email = new_email

    def update_subject(self, new_subject):
        c.execute("UPDATE teachers SET subject=? WHERE email=?",
                  (new_subject, self.email))
        conn.commit()
        self.subject = new_subject

    def update_password(self, new_password):
        hashed = hash_password(new_password)
        c.execute("UPDATE teachers SET password=? WHERE email=?",
                  (hashed, self.email))
        conn.commit()
        self.password = hashed

    def book_slot(self, day, hour, student_email):
        if not self.is_available(day, hour):
            print("Slot Already Taken")
            return False
        self.fill(day, hour)
        c.execute("""
                    INSERT INTO bookings (teacher_email, student_email, day, hour)
                    VALUES (?, ?, ?, ?)
                """, (self.email, student_email, day, hour))
        conn.commit()
        print("Slot Booked Successfully")
        return True

    def cancel_booking(self, day, hour, student_email):
        c.execute("""
                    DELETE FROM bookings
                    WHERE teacher_email=? AND student_email=? AND day=? AND hour=?
                """, (self.email, student_email, day, hour))
        conn.commit()
        self.empty(day, hour)
        print("Booking Canceled Successfully")

    def __str__(self):
        return f"Teacher({self.name}, {self.email}, {self.subject})"


class student:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password  # already hashed
        self.schedule = [[True] * 13 for _ in range(6)]

    def save_new_student(self):
        # Check if student already exists by email
        result = c.execute("SELECT email FROM students WHERE email=?",
                           (self.email,)).fetchone()

        if not result:
            schedule_str = list_to_string(self.schedule)
            c.execute("""
                INSERT INTO students (name, email, password, schedule)
                VALUES (?, ?, ?, ?)
            """, (self.name, self.email, self.password, schedule_str))
            conn.commit()
        else:
            # If exists, load schedule from DB
            self.load_schedule()

    def save_schedule(self):
        schedule_str = list_to_string(self.schedule)
        c.execute("UPDATE students SET schedule = ? WHERE email = ?",
                  (schedule_str, self.email))
        conn.commit()

    def load_schedule(self):
        row = c.execute(
            "SELECT schedule FROM students WHERE email=?",
            (self.email,)
        ).fetchone()
        if row:
            self.schedule = string_to_list(row[0])

    def fill(self, day, hour):
        self.schedule[day][hour] = False
        self.save_schedule()

    def empty(self, day, hour):
        self.schedule[day][hour] = True
        self.save_schedule()

    def is_available(self, day, hour):
        return self.schedule[day][hour]

    def get_available_slots(self):
        slots = []
        for d in range(6):
            for h in range(13):
                if self.schedule[d][h]:
                    slots.append((d, h))
        return slots

    def print_schedule(self):
        print(f"Schedule for {self.name}:")
        for day in self.schedule:
            print(" ".join("T" if x else "F" for x in day))

    def update_email(self, new_email):
        c.execute("UPDATE students SET email=? WHERE email=?",
                  (new_email, self.email))
        conn.commit()
        self.email = new_email

    def update_password(self, new_password):
        hashed = hash_password(new_password)
        c.execute("UPDATE students SET password=? WHERE email=?",
                  (hashed, self.email))
        conn.commit()
        self.password = hashed

    def options(self, subject, day, hour):
        teachers = c.execute("""
            SELECT name, email, subject FROM teachers
            WHERE subject = ?
        """, (subject,)).fetchall()
        available_teachers = []
        for t in teachers:
            teacher_obj = teacher(t[0], t[1], t[2], password=None)
            teacher_obj.load_schedule()
            if teacher_obj.is_available(day, hour) and self.is_available(day, hour):
                available_teachers.append(teacher_obj)
        return available_teachers

    def book(self, teacher_obj: teacher, day, hour):
        if not self.is_available(day, hour):
            print("Student is busy")
            return False
        if not teacher_obj.is_available(day, hour):
            print("Teacher is busy")
            return False
        # Mark student unavailable
        self.fill(day, hour)
        # Mark teacher unavailable via teacher.book_slot()
        teacher_obj.book_slot(day, hour, self.email)
        print("Booking successful!")
        return True

    def cancel(self, teacher_obj: teacher, day, hour):
        self.empty(day, hour)
        teacher_obj.cancel_booking(day, hour, self.email)

    def __str__(self):
        return f"Student({self.name}, {self.email})"
