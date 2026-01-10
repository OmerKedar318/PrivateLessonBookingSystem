from auth import *
from exceptions import *
from objects import *


class SessionManager:
    def __init__(self, conn):
        self.conn = conn
        self.c = conn.cursor()

    def get_teacher_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, subject, password
            FROM teachers
            WHERE email = ?
        """, (email,)).fetchone()

        if not row:
            return None

        name, email, subject, password = row
        return Teacher(name, email, subject, password, load_existing=True)

    def get_student_by_email(self, email):
        row = self.c.execute("""
            SELECT name, email, password
            FROM students
            WHERE email = ?
        """, (email,)).fetchone()

        if not row:
            return None

        name, email, password = row
        return Student(name, email, password, load_existing=True)

    def create_session(self, teacher_email, day, hour, capacity=5):
        # Enforce max 3 weekly sessions per teacher
        count = self.c.execute("""
            SELECT COUNT(*)
            FROM sessions
            WHERE teacher_email = ?
        """, (teacher_email,)).fetchone()[0]

        if count >= 3:
            raise SessionError("Teacher already has 3 weekly sessions")

        # Prevent duplicate time slots
        exists = self.c.execute("""
            SELECT 1
            FROM sessions
            WHERE teacher_email = ? AND day = ? AND hour = ?
        """, (teacher_email, day, hour)).fetchone()

        if exists:
            raise SessionError("Session already exists at this time")

        self.c.execute("""
                INSERT INTO sessions (teacher_email, subject, day, hour, capacity)
                VALUES (?, ?, ?, ?, ?)
            """, (teacher_email, self.get_teacher_by_email(teacher_email).subject, day, hour, capacity))

        self.conn.commit()

        session_id = self.c.lastrowid

        return session_id

    def delete_session(self, session_id, teacher_email):
        row = self.c.execute("""
            SELECT id
            FROM sessions
            WHERE id = ? AND teacher_email = ?
        """, (session_id, teacher_email)).fetchone()

        if not row:
            raise SessionError("Session not found or not owned by teacher")

        with self.conn:
            self.c.execute("""
                DELETE FROM session_students
                WHERE session_id = ?
            """, (session_id,))

            self.c.execute("""
                DELETE FROM sessions
                WHERE id = ?
            """, (session_id,))

    def get_sessions_for_teacher(self, teacher_email):
        rows = self.c.execute("""
            SELECT s.id, s.subject, s.capacity,
                   COUNT(ss.student_email) as enrolled
            FROM sessions s
            LEFT JOIN session_students ss ON s.id = ss.session_id
            WHERE s.teacher_email = ?
            GROUP BY s.id
            ORDER BY s.id
        """, (teacher_email,)).fetchall()

        return [
            {
                "id": r[0],
                "subject": r[1],
                "capacity": r[2],
                "enrolled": r[3],
            }
            for r in rows
        ]

    def get_sessions_for_student(self, student_email):
        rows = self.c.execute("""
            SELECT s.id, s.teacher_email, s.subject, s.capacity,
                   COUNT(ss2.student_email) as enrolled
            FROM sessions s
            JOIN session_students ss ON s.id = ss.session_id
            LEFT JOIN session_students ss2 ON s.id = ss2.session_id
            WHERE ss.student_email = ?
            GROUP BY s.id
            ORDER BY s.id
        """, (student_email,)).fetchall()

        return [
            {
                "id": r[0],
                "teacher_email": r[1],
                "subject": r[2],
                "capacity": r[3],
                "enrolled": r[4],
            }
            for r in rows
        ]

    def get_students_for_session(self, session_id, teacher_email):
        # Verify session belongs to teacher
        owns = self.c.execute("""
            SELECT 1
            FROM sessions
            WHERE id = ? AND teacher_email = ?
        """, (session_id, teacher_email)).fetchone()

        if not owns:
            raise SessionError("Session does not belong to this teacher")

        # Fetch enrolled students
        rows = self.c.execute("""
            SELECT s.name, s.email
            FROM session_students ss
            JOIN students s ON ss.student_email = s.email
            WHERE ss.session_id = ?
            ORDER BY s.name
        """, (session_id,)).fetchall()

        return [
            {"name": row[0], "email": row[1]}
            for row in rows
        ]

    def get_available_sessions(self, subject=None):
        if subject:
            rows = self.c.execute("""
                SELECT s.id, s.day, s.hour, s.capacity, t.subject, t.email
                FROM sessions s
                JOIN teachers t ON s.teacher_email = t.email
                WHERE t.subject = ?
                  AND s.id NOT IN (
                      SELECT session_id
                      FROM session_students
                      GROUP BY session_id
                      HAVING COUNT(*) >= s.capacity
                  )
            """, (subject,)).fetchall()
        else:
            rows = self.c.execute("""
                SELECT s.id, s.day, s.hour, s.capacity, t.subject, t.email
                FROM sessions s
                JOIN teachers t ON s.teacher_email = t.email
                WHERE s.id NOT IN (
                    SELECT session_id
                    FROM session_students
                    GROUP BY session_id
                    HAVING COUNT(*) >= s.capacity
                )
            """).fetchall()

        return [
            {
                "id": r[0],
                "day": r[1],
                "hour": r[2],
                "capacity": r[3],
                "subject": r[4],
                "teacher_email": r[5]
            }
            for r in rows
        ]

    def join_session(self, session_id, student_email):
        try:
            with self.conn:  # atomic transaction

                # Check session exists and get capacity
                row = self.c.execute("""
                    SELECT capacity
                    FROM sessions
                    WHERE id = ?
                """, (session_id,)).fetchone()

                if row is None:
                    raise SessionError("Session does not exist")

                capacity = row[0]

                # Count enrolled students
                enrolled = self.c.execute("""
                    SELECT COUNT(*)
                    FROM session_students
                    WHERE session_id = ?
                """, (session_id,)).fetchone()[0]

                if enrolled >= capacity:
                    raise SessionError("Session is full")

                # Single INSERT — DB enforces uniqueness
                self.c.execute("""
                    INSERT INTO session_students (session_id, student_email)
                    VALUES (?, ?)
                """, (session_id, student_email))

        except sqlite3.IntegrityError:
            # UNIQUE(session_id, student_email)
            raise SessionError("Student already enrolled in this session")

        except SessionError:
            raise  # rethrow clean errors

        except Exception as e:
            raise SessionError(f"Join session failed: {e}")

    def leave_session(self, session_id, student_email):
        try:
            with self.conn:

                # Verify enrollment exists
                row = self.c.execute("""
                    SELECT 1
                    FROM session_students
                    WHERE session_id = ? AND student_email = ?
                """, (session_id, student_email)).fetchone()

                if row is None:
                    raise SessionError("Student is not enrolled in this session")

                # Remove enrollment
                self.c.execute("""
                    DELETE FROM session_students
                    WHERE session_id = ? AND student_email = ?
                """, (session_id, student_email))

                self.conn.commit()

        except Exception as e:
            raise SessionError(f"Leave session failed: {e}")

    def get_student_sessions(self, student_email):
        return self.c.execute("""
            SELECT s.id, s.teacher_email, s.day, s.hour
            FROM sessions s
            JOIN session_students ss ON s.id = ss.session_id
            WHERE ss.student_email = ?
        """, (student_email,)).fetchall()

    def register_teacher(self, name, email, subject, password):
        if self.get_teacher_by_email(email):
            raise UserAlreadyExistsError("Teacher already exists")

        hashed = hash_password(password)

        self.c.execute("""
            INSERT INTO teachers (name, email, subject, password)
            VALUES (?, ?, ?, ?)
        """, (name, email, subject, hashed))

        self.conn.commit()

        return Teacher(name, email, subject, hashed, load_existing=True)

    def register_student(self, name, email, password):
        if self.get_student_by_email(email):
            raise UserAlreadyExistsError("Student already exists")

        hashed = hash_password(password)

        self.c.execute("""
            INSERT INTO students (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed))

        self.conn.commit()

        return Student(name, email, hashed, load_existing=True)

    def login_teacher(self, email, password):
        row = self.c.execute("""
            SELECT name, email, subject, password
            FROM teachers
            WHERE email = ?
        """, (email,)).fetchone()

        if not row:
            raise AuthenticationError("Invalid email or password")

        name, email, subject, stored_hash = row

        if not verify_password(password, stored_hash):
            raise AuthenticationError("Invalid email or password")

        return Teacher(name, email, subject, stored_hash, load_existing=True)

    def login_student(self, email, password):
        row = self.c.execute("""
                SELECT name, email, password
                FROM students
                WHERE email = ?
            """, (email,)).fetchone()

        if not row:
            raise UserNotFoundError("Student not found")

        name, email, stored_hash = row

        if not verify_password(password, stored_hash):
            raise AuthenticationError("Incorrect password")

        return Student(name, email, stored_hash, load_existing=True)
