from flask import Flask
from flask import request, session, redirect, url_for, render_template
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
            except Exception:
                user = manager.login_teacher(email, password)

            session["email"] = user.email
            return redirect("/dashboard")

        except Exception as e:
            return render_template("login.html", error=str(e))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    role = session.get("role")

    if role == "teacher":
        return redirect("/teacher")
    elif role == "student":
        return redirect("/student")
    else:
        return redirect("/login")


@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/login")
    return "Teacher dashboard"


@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/login")
    return "Student dashboard"


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
            return redirect("/dashboard")
        except Exception as e:
            return render_template("signup_teacher.html", error=str(e))

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
            return redirect("/dashboard")
        except Exception as e:
            return render_template("signup_student.html", error=str(e))

    return render_template("signup_student.html")


if __name__ == "__main__":
    app.run(debug=True)
