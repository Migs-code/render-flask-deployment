from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "school_system_secret_key"


def get_db():
    conn = sqlite3.connect("school.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            course TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    users = [
        ("admin", "admin123", "admin"),
        ("teacher", "teacher123", "teacher"),
        ("student", "student123", "student")
    ]

    for username, password, role in users:
        try:
            conn.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                """,
                (username, password, role)
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT * FROM users
            WHERE username = ? AND password = ?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")

            if user["role"] == "teacher":
                return redirect("/teacher")

            if user["role"] == "student":
                return redirect("/student")

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        if role not in ["student", "teacher"]:

            return render_template(
                "register.html",
                error="Invalid account type."
            )

        conn = get_db()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error="Username already exists."
            )

        conn.execute(
            """
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username, password, role)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()

    student_count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    teacher_count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'teacher'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        students=students,
        users=users,
        student_count=student_count,
        teacher_count=teacher_count
    )


@app.route("/teacher")
def teacher():

    if session.get("role") != "teacher":
        return redirect("/")

    conn = get_db()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    student_count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "teacher.html",
        students=students,
        student_count=student_count
    )


@app.route("/student")
def student():

    if session.get("role") != "student":
        return redirect("/")

    return render_template(
        "student.html",
        username=session.get("username")
    )


@app.route("/add_student", methods=["POST"])
def add_student():

    if session.get("role") not in ["admin", "teacher"]:
        return redirect("/")

    name = request.form["name"]
    age = request.form["age"]
    course = request.form["course"]
    email = request.form["email"]

    conn = get_db()

    conn.execute(
        """
        INSERT INTO students
        (name, age, course, email)
        VALUES (?, ?, ?, ?)
        """,
        (name, age, course, email)
    )

    conn.commit()
    conn.close()

    if session["role"] == "admin":
        return redirect("/admin")

    return redirect("/teacher")


@app.route("/delete_student/<int:id>")
def delete_student(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)