import sqlite3
from session_manager import SessionManager
from exceptions import SessionError, UserNotFoundError


def setup_manager():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    manager = SessionManager(conn)
    return manager


def test_teacher_register_and_login():
    mgr = setup_manager()

    teacher = mgr.register_teacher(
        name="Rachel",
        email="rachel@test.com",
        subject="CS",
        password="secret"
    )

    assert teacher.email == "rachel@test.com"

    logged_in = mgr.login_teacher("rachel@test.com", "secret")
    assert logged_in.email == teacher.email


def test_student_register():
    mgr = setup_manager()

    student = mgr.register_student(
        name="Alice",
        email="alice@test.com",
        password="1234"
    )

    assert student.email == "alice@test.com"


def test_create_session():
    mgr = setup_manager()

    teacher = mgr.register_teacher(
        "Rachel", "r@test.com", "CS", "pw"
    )

    session_id = mgr.create_session(
        teacher_email=teacher.email,
        day="Monday",
        hour=10,
        capacity=5
    )

    assert session_id is not None


def test_student_joins_session():
    mgr = setup_manager()

    teacher = mgr.register_teacher("Rachel", "r@test.com", "CS", "pw")
    student = mgr.register_student("Alice", "a@test.com", "pw")

    session_id = mgr.create_session(teacher.email, "Monday", 10, 5)

    mgr.join_session(session_id, student.email)

    sessions = mgr.get_sessions_for_student(student.email)
    assert len(sessions) == 1


def test_duplicate_join_fails():
    mgr = setup_manager()

    teacher = mgr.register_teacher("Rachel", "r@test.com", "CS", "pw")
    student = mgr.register_student("Alice", "a@test.com", "pw")

    session_id = mgr.create_session(teacher.email, "Monday", 10, 1)

    mgr.join_session(session_id, student.email)

    try:
        mgr.join_session(session_id, student.email)
        assert False, "Duplicate join should fail"
    except SessionError:
        pass


def test_capacity_enforced():
    mgr = setup_manager()

    teacher = mgr.register_teacher("Rachel", "r@test.com", "CS", "pw")

    s1 = mgr.register_student("A", "a@test.com", "pw")
    s2 = mgr.register_student("B", "b@test.com", "pw")

    session_id = mgr.create_session(teacher.email, "Monday", 10, 1)

    mgr.join_session(session_id, s1.email)

    try:
        mgr.join_session(session_id, s2.email)
        assert False, "Session should be full"
    except SessionError:
        pass


if __name__ == "__main__":
    test_teacher_register_and_login()
    test_student_register()
    test_create_session()
    test_student_joins_session()
    test_duplicate_join_fails()
    test_capacity_enforced()

    print("✅ All tests passed")
