from session_manager import *


def login_cli(manager):
    print("""Pick Role
1. Student
2. Teacher
""")
    role = input("> ").strip()

    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        if role == "1":
            user = manager.login_student(email, password)
        elif role == "2":
            user = manager.login_teacher(email, password)
        else:
            print("Invalid role")
            return None

        print("Login successful!")
        return user

    except ValueError as e:
        print(e)
        return None


def signup_cli(manager):
    print("""
Signup
1. Student
2. Teacher
""")
    role = input("> ").strip()

    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        if role == "1":
            user = manager.register_student(name, email, password)
        elif role == "2":
            subject = input("Subject: ").strip()
            user = manager.register_teacher(name, email, subject, password)
        else:
            print("Invalid role")
            return None

        print("Signup successful!")
        return user

    except ValueError as e:
        print(e)
        return None


def teacher_cli(manager, teacher):
    while True:
        print("""
Teacher Menu
1. Create session
2. View my sessions
3. Delete session
4. Logout
""")
        choice = input("> ").strip()

        if choice == "1":
            day = int(input("Day (0-5): "))
            hour = int(input("Hour (0-12): "))
            session_id = manager.create_session(teacher.email, day, hour)
            print(f"Session created (id={session_id})")

        elif choice == "2":
            sessions = manager.get_sessions_for_teacher(teacher.email)
            for s in sessions:
                print(s)

        elif choice == "3":
            session_id = int(input("Session ID to delete: "))
            teacher.delete_session(manager, session_id)
            print("Session deleted")

        elif choice == "4":
            break


def student_cli(manager, student):
    while True:
        print("""
Student Menu
1. View available sessions
2. Join session
3. Leave session
4. My sessions
5. Logout
""")
        choice = input("> ").strip()

        if choice == "1":
            subject = input("Subject: ")
            sessions = manager.get_available_sessions(subject)
            for s in sessions:
                print(s)

        elif choice == "2":
            session_id = int(input("Session ID to join: "))
            try:
                manager.join_session(session_id, student.email)
                print("Joined session successfully")
            except SessionError as e:
                print(e)

        elif choice == "3":
            session_id = int(input("Session ID to leave: "))
            manager.leave_session(session_id, student.email)
            print("Left session")

        elif choice == "4":
            sessions = manager.get_sessions_for_student(student.email)
            for s in sessions:
                print(s)

        elif choice == "5":
            break


def main():
    conn = sqlite3.connect("database.db")
    manager = SessionManager(conn)

    while True:
        print("""
Welcome
1. Login
2. Signup
3. Exit
""")
        choice = input("> ").strip()

        if choice == "1":
            user = login_cli(manager)
        elif choice == "2":
            user = signup_cli(manager)
        elif choice == "3":
            break
        else:
            continue

        if not user:
            continue

        if isinstance(user, Teacher):
            teacher_cli(manager, user)
        else:
            student_cli(manager, user)


if __name__ == "__main__":
    main()
