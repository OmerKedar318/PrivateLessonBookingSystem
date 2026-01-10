def create_tables(conn):
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        day TEXT NOT NULL,
        hour INTEGER NOT NULL,
        capacity INTEGER NOT NULL,
        FOREIGN KEY (teacher_email) REFERENCES teachers(email)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS session_students (
        session_id INTEGER,
        student_email TEXT,
        PRIMARY KEY (session_id, student_email),
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (student_email) REFERENCES students(email)
    )
    """)

    conn.commit()
