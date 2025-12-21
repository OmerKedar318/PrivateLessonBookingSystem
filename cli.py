from booking_manager import *


def main_menu():
    print("\n=== Private Lessons Booking System ===")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    return input("Choose: ")


def teacher_menu():
    print("\n--- Teacher Menu ---")
    print("1. View schedule")
    print("2. View bookings")
    print("3. Cancel booking")
    print("4. Logout")
    return input("Choose: ")


def student_menu():
    print("\n--- Student Menu ---")
    print("1. View schedule")
    print("2. Find available teachers")
    print("3. Book lesson")
    print("4. View my bookings")
    print("5. Cancel booking")
    print("6. Logout")
    return input("Choose: ")


def register(mgr):
    print("\nRegister as:")
    print("1. Teacher")
    print("2. Student")
    choice = input("Choose: ")

    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")

    if choice == "1":
        subject = input("Subject: ")
        success = mgr.register_teacher(name, email, subject, password)
    else:
        success = mgr.register_student(name, email, password)

    if success:
        print("Registration successful")
    else:
        print("Email already exists")


def login(mgr):
    print("\nLogin as:")
    print("1. Teacher")
    print("2. Student")
    choice = input("Choose: ")

    email = input("Email: ")
    password = input("Password: ")

    if choice == "1":
        user = mgr.login_teacher(email, password)
        role = "teacher"
    else:
        user = mgr.login_student(email, password)
        role = "student"

    if user is None:
        print("User not found")
        return None, None
    if user is False:
        print("Wrong password")
        return None, None

    print(f"Logged in as {user.name}")
    return user, role


def teacher_session(mgr, teacher_obj):
    while True:
        choice = teacher_menu()

        if choice == "1":
            teacher_obj.print_schedule()

        elif choice == "2":
            bookings = mgr.get_bookings_for_teacher(teacher_obj.email)
            for b in bookings:
                print(b)

        if choice == "3":
            bookings = mgr.get_bookings_for_teacher(teacher_obj.email)
            if not bookings:
                print("No bookings.")
                continue

            for i, b in enumerate(bookings):
                print(f"{i}. Student: {b['student_email']} | Day {b['day']} Hour {b['hour']}")
            idx = int(input("Choose booking number: "))
            b = bookings[idx]
            student_obj = mgr.get_student_by_email(b["student_email"])
            mgr.cancel(teacher_obj, student_obj, b["day"], b["hour"])
            print("Booking canceled")

        elif choice == "4":
            break


def student_session(mgr, student_obj):
    while True:
        choice = student_menu()

        if choice == "1":
            student_obj.print_schedule()

        elif choice == "2":
            subject = input("Subject: ")
            day = int(input("Day (0-5): "))
            hour = int(input("Hour (0-12): "))

            teachers = student_obj.options(subject, day, hour)
            for t in teachers:
                print(t)

        elif choice == "3":
            teacher_email = input("Teacher email: ")
            day = int(input("Day (0-5): "))
            hour = int(input("Hour (0-12): "))

            teacher_obj = mgr.get_teacher_by_email(teacher_email)
            if teacher_obj:
                if mgr.book(teacher_obj, student_obj, day, hour):
                    print("Lesson booked")
                else:
                    print("Slot unavailable")

        elif choice == "4":
            bookings = mgr.get_bookings_for_student(student_obj.email)
            for b in bookings:
                print(b)

        if choice == "5":
            bookings = mgr.get_bookings_for_student(student_obj.email)
            if not bookings:
                print("No bookings to cancel.")
                continue

            for i, b in enumerate(bookings):
                print(f"{i}. Teacher: {b['teacher_email']} | Day {b['day']} Hour {b['hour']}")
            idx = int(input("Choose booking number: "))
            b = bookings[idx]
            teacher_obj = mgr.get_teacher_by_email(b["teacher_email"])
            mgr.cancel(teacher_obj, student_obj, b["day"], b["hour"])
            print("Booking canceled")

        elif choice == "6":
            break


def run():
    mgr = BookingManager(conn)

    while True:
        choice = main_menu()

        if choice == "1":
            register(mgr)

        elif choice == "2":
            user, role = login(mgr)
            if user:
                if role == "teacher":
                    teacher_session(mgr, user)
                else:
                    student_session(mgr, user)

        elif choice == "3":
            print("Goodbye!")
            break


if __name__ == "__main__":
    run()
