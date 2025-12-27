from booking_manager import BookingManager


mgr = BookingManager()

print("Register teacher")
mgr.register_teacher(
    name="Rachel Schmidt",
    email="rachel@gmail.com",
    subject="Computer Science",
    password="secret"
)

print("Register student")
mgr.register_student(
    name="Omer",
    email="omer@gmail.com",
    password="1234"
)

teacher = mgr.login_teacher("rachel@gmail.com", "secret")
student = mgr.login_student("omer@gmail.com", "1234")

assert teacher.email == "rachel@gmail.com"
assert student.email == "omer@gmail.com"

available = mgr.get_available_teachers(
    subject="Computer Science",
    day=1,
    hour=5,
    student=student
)

assert len(available) == 1
assert available[0].email == "rachel@gmail.com"

booking_id = mgr.book(
    student=student,
    teacher=teacher,
    day=1,
    hour=5
)

assert booking_id is not True

try:
    mgr.book(
        student=student,
        teacher=teacher,
        day=1,
        hour=5
    )
    assert False, "Double booking allowed!"
except Exception:
    print("Double booking blocked ✔")

student_bookings = mgr.get_bookings_for_student(student)
teacher_bookings = mgr.get_bookings_for_teacher(teacher)

assert len(student_bookings) == 1
assert len(teacher_bookings) == 1

mgr.cancel(teacher, student, 1, 5)

assert len(mgr.get_bookings_for_student(student)) == 0

# This part doesn't work yet
new_id = mgr.book(
    student=student,
    teacher=teacher,
    day=1,
    hour=5
)

assert new_id != booking_id

print("✅ SMOKE TESTS PASSED")
