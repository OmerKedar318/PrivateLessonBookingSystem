from objects import *

conn = sqlite3.connect('database.db')
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_email TEXT NOT NULL,
    student_email TEXT NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    FOREIGN KEY (teacher_email) REFERENCES teachers(email) ON DELETE CASCADE,
    FOREIGN KEY (student_email) REFERENCES students(email) ON DELETE CASCADE,
    UNIQUE (teacher_email, day, hour),
    UNIQUE (student_email, day, hour)
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    name TEXT NOT NULL,
    email TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    password TEXT NOT NULL,
    schedule TEXT NOT NULL
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT NOT NULL,
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    schedule TEXT NOT NULL
);
""")

conn.commit()
conn.close()
