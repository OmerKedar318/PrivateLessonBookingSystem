import time
from datetime import timedelta
from flask import Flask
from flask import request, session, redirect, url_for, render_template, flash
from flask_wtf.csrf import CSRFProtect
import sqlite3
from schema import create_tables
from session_manager import SessionManager
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY"),
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE") == "True",
    SESSION_COOKIE_HTTPONLY=os.getenv("SESSION_COOKIE_HTTPONLY") == "True",
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE"),
    ENV=os.getenv("FLASK_ENV"),
    DEBUG=os.getenv("FLASK_DEBUG") == "True",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)

csrf = CSRFProtect(app)


def get_manager():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    return SessionManager(conn)


def setup_logging(app):
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10240,  # 10KB before rotating
        backupCount=5  # Keep 5 old logs
    )

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)

    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging is set up successfully.")


setup_logging(app)


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    manager = get_manager()
    if "login_attempts" not in session:
        session["login_attempts"] = 0

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            # Attempt login
            try:
                user = manager.login_student(email, password)
                session["role"] = "student"
            except Exception:
                user = manager.login_teacher(email, password)
                session["role"] = "teacher"

            session["login_attempts"] = 0
            session.permanent = True
            session["email"] = user.email

            # LOG: Successful login
            app.logger.info(f"User logged in: {email} (Role: {session['role']})")

            flash("Logged in successfully", "success")
            return redirect("/dashboard")

        except Exception as e:
            session["login_attempts"] = session.get("login_attempts", 0) + 1

            # LOG: Failed attempt with severity increase if throttled
            app.logger.warning(f"Failed login attempt #{session['login_attempts']} for: {email}")

            if session["login_attempts"] > 5:
                app.logger.error(f"Brute force protection triggered for: {email}")
                time.sleep(3)
            flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    app.logger.info(f"User logged out: {session['email']} (Role: {session['role']})")
    session.clear()
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    role = session.get("role")

    if role == "teacher":
        return redirect(url_for("teacher_dashboard"))
    elif role == "student":
        return redirect(url_for("student_dashboard"))
    else:
        return redirect(url_for("login"))


@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    teacher = manager.get_teacher_by_email(session["email"])

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher
    )


@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")

    manager = get_manager()
    student = manager.get_student_by_email(session["email"])

    return render_template(
        "student_dashboard.html",
        student=student
    )


@app.route("/signup")
def signup():
    return render_template("signup_choice.html")


@app.route("/signup/teacher", methods=["GET", "POST"])
def signup_teacher():
    manager = get_manager()
    if request.method == "POST":
        try:
            teacher = manager.register_teacher(
                request.form["name"], request.form["email"],
                request.form["subject"], request.form["password"]
            )
            session["email"] = teacher.email
            session["role"] = "teacher"

            # LOG: New registration
            app.logger.info(f"New teacher registered: {teacher.email}")

            flash("Account created successfully!", "success")
            return redirect("/dashboard")
        except Exception as e:
            app.logger.error(f"Teacher signup failed: {str(e)}")
            flash(str(e), "error")
    return render_template("signup_teacher.html")


@app.route("/signup/student", methods=["GET", "POST"])
def signup_student():
    manager = get_manager()

    if request.method == "POST":
        try:
            student = manager.register_student(
                request.form["name"],
                request.form["email"],
                request.form["password"]
            )
            session["email"] = student.email
            session["role"] = "student"

            # LOG: New registration
            app.logger.info(f"New student registered: {student.email}")

            flash("Account created successfully!", "success")
            return redirect("/dashboard")
        except Exception as e:
            app.logger.error(f"Teacher signup failed: {str(e)}")
            flash(str(e), "error")

    return render_template("signup_student.html")


@app.route("/sessions")
def sessions():
    if session.get("role") != "student":
        return redirect("/login")

    manager = get_manager()

    # Get search query (can be empty)
    query = request.args.get("q", "").strip()

    # Fetch sessions (all if no query)
    sessions = manager.get_available_sessions(
        student_email=session["email"],
        subject=query if query else None
    )

    # Fixed ranges
    days = list(range(6))  # 0–5 (Sunday–Friday)
    hours = list(range(13))  # 0–12

    # Build lookup table: (day, hour) -> session
    schedule = {}
    for s in sessions:
        schedule[(s["day"], s["hour"])] = s

    day_names = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "_sessions_table.html",
            days=days,
            hours=hours,
            schedule=schedule,
            day_names=day_names,
            sessions=sessions
        )

    return render_template(
        "sessions.html",
        days=days,
        hours=hours,
        schedule=schedule,
        day_names=day_names,
        sessions=sessions,
        query=query
    )


@app.route("/join/<int:session_id>", methods=["POST"])
def join_session(session_id):
    if session.get("role") != "student":
        app.logger.warning(f"Unauthorized session join attempt by {session.get('email', 'Guest')}")
        return redirect("/login")

    manager = get_manager()
    try:
        manager.join_session(session_id, session["email"])
        # LOG: Student activity
        app.logger.info(f"Student {session['email']} joined session {session_id}")
        flash("Joined session successfully!", "success")
    except Exception as e:
        app.logger.error(f"Error joining session {session_id} for {session['email']}: {str(e)}")
        flash(str(e), "error")
    return redirect("/sessions")


@app.route("/my_sessions")
def my_sessions():
    if session.get("role") != "student":
        return redirect("/login")

    manager = get_manager()
    sessions = manager.get_sessions_for_student(session["email"])

    days = list(range(6))  # Sunday–Friday
    hours = list(range(13))  # 0–12

    schedule = {}
    for s in sessions:
        schedule[(s["day"], s["hour"])] = s

    day_names = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
    }

    return render_template(
        "my_sessions.html",
        days=days,
        hours=hours,
        schedule=schedule,
        day_names=day_names
    )


@app.route("/leave_session/<int:session_id>", methods=["POST"])
def leave_session(session_id):
    if session.get("role") != "student":
        app.logger.warning(f"Unauthorized attempt to leave session {session_id}")
        return redirect("/login")

    manager = get_manager()
    try:
        manager.leave_session(session_id, session["email"])
        app.logger.info(f"Student {session['email']} left session {session_id}")
    except Exception as e:
        app.logger.error(f"Error: {session['email']} failed to leave session {session_id}: {str(e)}")
        return str(e)

    return redirect("/my_sessions")


@app.route("/teacher_sessions")
def teacher_my_sessions():
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    sessions = manager.get_sessions_for_teacher(session["email"])

    days = list(range(6))  # Sunday–Friday
    hours = list(range(13))  # 0–12

    schedule = {}
    for s in sessions:
        schedule[(s["day"], s["hour"])] = s

    day_names = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
    }

    return render_template(
        "teacher_sessions.html",
        days=days,
        hours=hours,
        schedule=schedule,
        day_names=day_names
    )


@app.route("/teacher/view_students/<int:session_id>")
def view_students(session_id):
    if session.get("role") != "teacher":
        app.logger.warning(f"Unauthorized access attempt to student list by {session.get('email')}")
        return redirect("/login")

    app.logger.info(f"Teacher {session['email']} viewing students for session {session_id}")

    manager = get_manager()
    students = manager.get_students_for_session(session_id, session["email"])

    return render_template("view_students.html", students=students)


@app.route("/teacher/delete_session/<int:session_id>", methods=["POST"])
def delete_session(session_id):
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    try:
        manager.delete_session(session_id, session["email"])
        # LOG: Resource deletion
        app.logger.info(f"Teacher {session['email']} deleted session {session_id}")
    except Exception as e:
        app.logger.error(f"Failed to delete session {session_id}: {str(e)}")

    return redirect("/teacher_sessions")


@app.route("/create_session", methods=["GET", "POST"])
def create_session():
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    teacher_email = session["email"]

    # Get teacher object
    teacher = manager.get_teacher_by_email(teacher_email)

    # Get existing sessions for grid blocking
    sessions = manager.get_sessions_for_teacher(teacher_email)
    taken = [(s["day"], s["hour"]) for s in sessions]

    if request.method == "POST":
        day = int(request.form["day"])
        hour = int(request.form["hour"])

        try:
            manager.create_session(teacher_email, day, hour)

            # LOG: Resource creation
            app.logger.info(
                f"Teacher {teacher_email} created session: Day {day}, Hour {hour}"
            )

            return redirect("/teacher_sessions")

        except Exception as e:
            app.logger.error(
                f"Session creation failed for {teacher_email}: {str(e)}"
            )
            flash(str(e), "error")

    return render_template(
        "create_session.html",
        teacher=teacher,
        taken=taken
    )


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return "Internal Server Error", 500


@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"Page not found: {request.url}")
    return "Page Not Found", 404


if __name__ == "__main__":
    app.run(debug=True)
