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


class Teacher:
    def __init__(self, name, email, subject, password):
        self.name = name
        self.email = email
        self.subject = subject
        self.password = password
        self.schedule = [[True] * 13 for _ in range(6)]

    def load_schedule(self):
        row = c.execute(
            "SELECT schedule FROM teachers WHERE email=?",
            (self.email,)
        ).fetchone()
        if row:
            self.schedule = string_to_list(row[0])

    def fill(self, day, hour):
        self.schedule[day][hour] = False
        # Don't forget to update the schedule!

    def empty(self, day, hour):
        self.schedule[day][hour] = True
        # Don't forget to update the schedule!

    def is_available(self, day, hour):
        return self.schedule[day][hour]

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


class Student:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password  # already hashed
        self.schedule = [[True] * 13 for _ in range(6)]

    def load_schedule(self):
        row = c.execute(
            "SELECT schedule FROM students WHERE email=?",
            (self.email,)
        ).fetchone()
        if row:
            self.schedule = string_to_list(row[0])

    def fill(self, day, hour):
        self.schedule[day][hour] = False
        # Don't forget to update the schedule!

    def empty(self, day, hour):
        self.schedule[day][hour] = True
        # Don't forget to update the schedule!

    def is_available(self, day, hour):
        return self.schedule[day][hour]

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

    # def options(self, subject, day, hour):
    #     teachers = c.execute("""
    #         SELECT name, email, subject FROM teachers
    #         WHERE subject = ?
    #     """, (subject,)).fetchall()
    #     available_teachers = []
    #     for t in teachers:
    #         teacher_obj = Teacher(t[0], t[1], t[2], password=None)
    #         teacher_obj.load_schedule()
    #         if teacher_obj.is_available(day, hour) and self.is_available(day, hour):
    #             available_teachers.append(teacher_obj)
    #     return available_teachers

    def __str__(self):
        return f"Student({self.name}, {self.email})"
