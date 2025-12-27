from booking_manager import *


def get_int(prompt, min_val, max_val):
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            print(f"Enter a number between {min_val} and {max_val}")
        except ValueError:
            print("Invalid number")


def choose_booking_index(max_index):
    while True:
        try:
            idx = int(input("Choose: "))
            if 0 <= idx < max_index:
                return idx
            print("Invalid choice")
        except ValueError:
            print("Enter a number")


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

    try:
        if choice == "1":
            user = mgr.login_teacher(email, password)
            role = "teacher"
        else:
            user = mgr.login_student(email, password)
            role = "student"
        print(f"Logged in as {user.name}")
        return user, role

    except UserNotFoundError as e:
        print(e)

    except AuthenticationError as e:
        print(e)

    return None


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
            idx = choose_booking_index(len(bookings))
            b = bookings[idx]
            student_obj = mgr.get_student_by_email(b["student_email"])
            try:
                mgr.cancel(teacher_obj, student_obj, b["day"], b["hour"])
                print("Booking canceled")
            except AuthenticationError as e:
                print(e)
            except BookingError as e:
                print(e)

        elif choice == "4":
            break


def student_session(mgr, student_obj):
    while True:
        choice = student_menu()

        if choice == "1":
            student_obj.print_schedule()

        elif choice == "2":
            subject = input("Subject: ")
            day = get_int("Day (0-5): ", 0, 5)
            hour = get_int("Hour (0-12): ", 0, 12)

            teachers = mgr.get_available_teachers(subject, day, hour, student_obj)
            for t in teachers:
                print(t)

        elif choice == "3":
            teacher_email = input("Teacher email: ")
            day = int(input("Day (0-5): "))
            hour = int(input("Hour (0-12): "))

            teacher_obj = mgr.get_teacher_by_email(teacher_email)
            try:
                mgr.book(teacher_obj, student_obj, day, hour)
                print("Booking Successful")
            except Exception as e:
                print(e)

        elif choice == "4":
            bookings = mgr.get_bookings_for_student(student_obj.email)
            for b in bookings:
                print(b)

        if choice == "5":
            bookings = mgr.get_bookings_for_student(student_obj.email)
            if not bookings:
                print("No bookings to cancel")
                continue

            for i, b in enumerate(bookings):
                print(f"{i}. Teacher: {b['teacher_email']} | Day {b['day']} Hour {b['hour']}")
            idx = choose_booking_index(len(bookings))
            b = bookings[idx]
            teacher_obj = mgr.get_teacher_by_email(b["teacher_email"])
            try:
                mgr.cancel(teacher_obj, student_obj, b["day"], b["hour"])
                print("Booking canceled")
            except AuthenticationError as e:
                print(e)
            except BookingError as e:
                print(e)

        elif choice == "6":
            break


def run():
    mgr = BookingManager()

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
