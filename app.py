from flask import Flask
from flask import request, session, redirect, url_for, render_template, flash
import sqlite3
from schema import create_tables
from session_manager import SessionManager

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # change later


def get_manager():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    return SessionManager(conn)


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    manager = get_manager()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            try:
                user = manager.login_student(email, password)
                session["role"] = "student"
            except Exception:
                user = manager.login_teacher(email, password)
                session["role"] = "teacher"

            session["email"] = user.email
            flash("Logged in successfully", "success")
            return redirect("/dashboard")

        except Exception as e:
            flash(str(e), "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
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
                request.form["name"],
                request.form["email"],
                request.form["subject"],
                request.form["password"]
            )
            session["email"] = teacher.email
            session["role"] = "teacher"
            flash("Account created successfully!", "success")
            return redirect("/dashboard")
        except Exception as e:
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
            flash("Account created successfully!", "success")
            return redirect("/dashboard")
        except Exception as e:
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
    days = list(range(6))       # 0–5 (Sunday–Friday)
    hours = list(range(13))     # 0–12

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
        return redirect("/login")

    manager = get_manager()

    try:
        manager.join_session(session_id, session["email"])
        flash("Joined session successfully!", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect("/sessions")


@app.route("/my_sessions")
def my_sessions():
    if session.get("role") != "student":
        return redirect("/login")

    manager = get_manager()
    sessions = manager.get_sessions_for_student(session["email"])

    return render_template("my_sessions.html", sessions=sessions)


@app.route("/leave_session/<int:session_id>")
def leave_session(session_id):
    if session.get("role") != "student":
        return redirect("/login")

    manager = get_manager()
    try:
        manager.leave_session(session_id, session["email"])
    except Exception as e:
        return str(e)

    return redirect("/my_sessions")


@app.route("/teacher_sessions")
def teacher_sessions():
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    sessions = manager.get_sessions_for_teacher(session["email"])

    return render_template("teacher_sessions.html", sessions=sessions)


@app.route("/delete_session/<int:session_id>")
def delete_session(session_id):
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    try:
        manager.delete_session(session_id, session["email"])
    except Exception as e:
        return str(e)

    return redirect("/teacher_sessions")


@app.route("/create_session", methods=["GET", "POST"])
def create_session():
    if session.get("role") != "teacher":
        return redirect("/login")

    manager = get_manager()
    teacher = manager.get_teacher_by_email(session["email"])

    if request.method == "POST":
        try:
            manager.create_session(
                teacher_email=teacher.email,
                day=request.form["day"],
                hour=request.form["hour"],
            )
            return redirect("/teacher")
        except Exception as e:
            return render_template(
                "create_session.html",
                teacher=teacher,
                error=str(e)
            )

    return render_template("create_session.html", teacher=teacher)


if __name__ == "__main__":
    app.run(debug=True)
