import sqlite3
from auth import hash_password


conn = sqlite3.connect('database.db')
c = conn.cursor()


class Teacher:
    def __init__(self, name, email, subject, password, load_existing=False):
        self.role = "teacher"
        self.name = name
        self.email = email
        self.subject = subject
        self.password = password

        if not load_existing:
            self.save()

    def save(self):
        c.execute("""
            INSERT INTO teachers (email, name, subject, password)
            VALUES (?, ?, ?, ?)
        """, (self.email, self.name, self.subject, self.password))

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

    def create_session(self, manager, day, hour, capacity=5):
        manager.create_session(
            teacher_email=self.email,
            day=day,
            hour=hour,
            capacity=capacity
        )

    def delete_session(self, manager, session_id):
        manager.delete_session(session_id, self.email)

    def get_sessions(self, manager):
        return manager.get_sessions_for_teacher(self.email)

    def view_session_students(self, manager, session_id):
        return manager.get_students_for_session(
            session_id=session_id,
            teacher_email=self.email
        )


class Student:
    def __init__(self, name, email, password, load_existing=False):
        self.role = "student"
        self.name = name
        self.email = email
        self.password = password

        if not load_existing:
            self.save()

    def save(self):
        c.execute("""
            INSERT INTO students (email, name, password)
            VALUES (?, ?, ?)
        """, (self.email, self.name, self.password))

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

    def available_sessions(self, manager):
        return manager.get_available_sessions()

    def join_session(self, manager, session_id):
        manager.join_session(session_id, self.email)

    def leave_session(self, manager, session_id):
        manager.leave_session(session_id, self.email)

    def my_sessions(self, manager):
        return manager.get_sessions_for_student(self.email)


class Session:
    def __init__(self, id, teacher_email, day, hour, capacity, enrolled):
        self.id = id
        self.teacher_email = teacher_email
        self.day = day
        self.hour = hour
        self.capacity = capacity
        self.enrolled = enrolled

    @property
    def spots_left(self):
        return self.capacity - self.enrolled

    def is_full(self):
        return self.enrolled >= self.capacity

    def __str__(self):
        return (
            f"Session #{self.id} | "
            f"Teacher: {self.teacher_email} | "
            f"Day {self.day}, Hour {self.hour} | "
            f"{self.spots_left} spots left"
        )
