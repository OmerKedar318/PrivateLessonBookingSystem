from objects import *

conn = sqlite3.connect('database.db')
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    email TEXT PRIMARY KEY,
    name TEXT,
    subject TEXT,
    password TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS students (
    email TEXT PRIMARY KEY,
    name TEXT,
    password TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_email TEXT,
    day INTEGER,
    hour INTEGER,
    capacity INTEGER DEFAULT 5,
    FOREIGN KEY (teacher_email) REFERENCES teachers(email)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS session_students (
    session_id INTEGER,
    student_email TEXT,
    PRIMARY KEY (session_id, student_email),
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (student_email) REFERENCES students(email)
);
""")

c.execute("""
CREATE UNIQUE INDEX idx_teacher_time
ON sessions (teacher_email, day, hour
);
""")

conn.commit()
conn.close()
