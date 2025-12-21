import sqlite3
from objects import *

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    name TEXT,
    email TEXT PRIMARY KEY,
    subject TEXT,
    password TEXT,
    schedule TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT,
    email TEXT PRIMARY KEY,
    password TEXT,
    schedule TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_email TEXT,
    student_email TEXT,
    day INTEGER,
    hour INTEGER
);
""")

conn.commit()
conn.close()
