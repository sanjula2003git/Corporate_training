# =====================================================================
# database.py  —  the connection to the real database + first-time seeding
#
# BUSINESS LEVEL: This sets up the filing cabinet (a single file: training.db)
#   and, the very first time, fills it with starter records. After that the
#   data lives on disk and SURVIVES server restarts — the whole point of a DB.
#
# CODE LEVEL: Creates a SQLite engine, a session factory, table creation, and
#   an idempotent seed (only seeds if empty).
#
# This stage seeds a REAL login for every student and trainer (so each person
# signs in and sees only their own data), plus sample materials, assignments,
# submissions, online classes and per-student attendance to power the three
# role dashboards.
#
# 👀 TEACHING TIP: set echo=True below to watch the actual SQL the ORM runs
#    (CREATE TABLE, INSERT, SELECT...) print live in the console.
# =====================================================================
import bcrypt
from sqlmodel import SQLModel, create_engine, Session, select

from models import (UserDB, StudentDB, TrainerDB, CourseDB, CertificateDB,
                    AttendanceDB, MaterialDB, AssignmentDB, SubmissionDB,
                    ClassSessionDB)

# The database is just one file sitting next to this code.
DATABASE_URL = "sqlite:///training.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,                                   # ← flip to True to SEE the SQL
    connect_args={"check_same_thread": False},    # needed for SQLite + FastAPI
)


def get_session():
    # BUSINESS: open a drawer, do your work, close it. One session per request.
    with Session(engine) as session:
        yield session


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_db():
    # 1) Create the tables (drawers) if they don't exist yet.
    SQLModel.metadata.create_all(engine)

    # 2) Seed starter data ONLY if the database is empty (first run).
    with Session(engine) as session:
        already = session.exec(select(UserDB)).first()
        if already:
            return  # already seeded — don't duplicate

        # --- students (each also gets a login below) ---
        students = [
            StudentDB(id="STU-001", name="Ravi Kumar",  email="ravi.kumar@example.com",  course="React Fundamentals", status="Active"),
            StudentDB(id="STU-002", name="Meera Nair",  email="meera.nair@example.com",  course="Python Basics",      status="Active"),
            StudentDB(id="STU-003", name="John Mathew", email="john.mathew@example.com", course="Java Backend",       status="Inactive"),
            StudentDB(id="STU-004", name="Aisha Khan",  email="aisha.khan@example.com",  course="React Fundamentals", status="Active"),
            StudentDB(id="STU-005", name="David Lee",   email="david.lee@example.com",   course="Java Backend",       status="Active"),
        ]
        session.add_all(students)

        # --- trainers (each also gets a login below) ---
        trainers = [
            TrainerDB(id="TRN-001", name="Anita Sharma", expertise="Java, Spring Boot",    courses="Java Backend, Microservices"),
            TrainerDB(id="TRN-002", name="Suresh Rao",   expertise="React, JavaScript",    courses="React Fundamentals"),
            TrainerDB(id="TRN-003", name="Priya Menon",  expertise="Python, Data Science", courses="Python Basics, ML 101"),
        ]
        session.add_all(trainers)

        # --- courses (trainer = who teaches it) ---
        session.add_all([
            CourseDB(id="CRS-001", name="React Fundamentals", trainer="Suresh Rao",   duration="6 Weeks", status="Ongoing"),
            CourseDB(id="CRS-002", name="Java Backend",       trainer="Anita Sharma", duration="8 Weeks", status="Ongoing"),
            CourseDB(id="CRS-003", name="Python Basics",      trainer="Priya Menon",  duration="4 Weeks", status="Completed"),
        ])

        # --- users / logins ---
        #   • two ADMINS (the brief: a second admin with the same powers)
        #   • one login per trainer, linked to their TRN-xxx record
        #   • one login per student, linked to their STU-xxx record
        session.add_all([
            UserDB(username="admin",     name="System Admin",   role="admin",   password_hash=hash_password("admin123")),
            UserDB(username="superuser", name="Super User",     role="admin",   password_hash=hash_password("superuser123")),

            UserDB(username="anita",  name="Anita Sharma", role="trainer", password_hash=hash_password("trainer123"), ref_id="TRN-001"),
            UserDB(username="suresh", name="Suresh Rao",   role="trainer", password_hash=hash_password("trainer123"), ref_id="TRN-002"),
            UserDB(username="priya",  name="Priya Menon",  role="trainer", password_hash=hash_password("trainer123"), ref_id="TRN-003"),

            UserDB(username="ravi",  name="Ravi Kumar",  role="student", password_hash=hash_password("student123"), ref_id="STU-001"),
            UserDB(username="meera", name="Meera Nair",  role="student", password_hash=hash_password("student123"), ref_id="STU-002"),
            UserDB(username="john",  name="John Mathew", role="student", password_hash=hash_password("student123"), ref_id="STU-003"),
            UserDB(username="aisha", name="Aisha Khan",  role="student", password_hash=hash_password("student123"), ref_id="STU-004"),
            UserDB(username="david", name="David Lee",   role="student", password_hash=hash_password("student123"), ref_id="STU-005"),
        ])

        # --- certificates ---
        session.add_all([
            CertificateDB(student="Meera Nair",  course="Python Basics",      status="Completed"),
            CertificateDB(student="Ravi Kumar",  course="React Fundamentals", status="In Progress"),
            CertificateDB(student="John Mathew", course="Java Backend",       status="Completed"),
        ])

        # --- course materials: real, commonly-used free learning resources ---
        session.add_all([
            MaterialDB(course="React Fundamentals", title="Learn React — Official Docs",                 kind="Document", url="https://react.dev/learn",                          description="Official interactive React tutorial: components, props, state and hooks.", uploaded_by="Suresh Rao"),
            MaterialDB(course="React Fundamentals", title="React Full Course for Beginners (freeCodeCamp)", kind="Video",  url="https://www.youtube.com/watch?v=bMknfKXIFA8",      description="Free end-to-end React video course.",        uploaded_by="Suresh Rao"),
            MaterialDB(course="Java Backend",       title="Building a RESTful Web Service (Spring Guide)", kind="Document", url="https://spring.io/guides/gs/rest-service",        description="Official Spring getting-started guide for a REST API.", uploaded_by="Anita Sharma"),
            MaterialDB(course="Java Backend",       title="Spring Boot Reference Documentation",          kind="Link",     url="https://docs.spring.io/spring-boot/index.html",   description="The complete official Spring Boot docs.",    uploaded_by="Anita Sharma"),
            MaterialDB(course="Python Basics",      title="The Python Tutorial — Official Docs",          kind="Document", url="https://docs.python.org/3/tutorial/",             description="The official Python tutorial from python.org.", uploaded_by="Priya Menon"),
            MaterialDB(course="Python Basics",      title="Learn Python — Full Course (freeCodeCamp)",    kind="Video",    url="https://www.youtube.com/watch?v=rfscVS0vtbw",     description="Popular 4-hour Python course for beginners.", uploaded_by="Priya Menon"),
        ])

        # --- assignments (trainer -> course) ---
        assignments = [
            AssignmentDB(id=1, course="React Fundamentals", title="Build a Counter Component", description="Create a <Counter/> with increment/decrement using useState.", due_date="2026-06-12", max_marks=100, created_by="Suresh Rao"),
            AssignmentDB(id=2, course="React Fundamentals", title="Todo List App",             description="Build a todo list with add/delete. Submit a link to your repo.", due_date="2026-06-20", max_marks=100, created_by="Suresh Rao"),
            AssignmentDB(id=3, course="Java Backend",       title="CRUD REST Controller",      description="Implement a Spring Boot CRUD controller for a Book entity.",     due_date="2026-06-15", max_marks=100, created_by="Anita Sharma"),
            AssignmentDB(id=4, course="Python Basics",      title="FizzBuzz + Functions",      description="Write FizzBuzz and three reusable helper functions.",           due_date="2026-06-08", max_marks=100, created_by="Priya Menon"),
        ]
        session.add_all(assignments)

        # --- submissions (some graded, some pending review) ---
        session.add_all([
            # Ravi (React) — one graded, one still pending review
            SubmissionDB(assignment_id=1, student_id="STU-001", student_name="Ravi Kumar", content="Implemented Counter with useState.", link="https://github.com/ravi/counter", status="Graded",    marks=88, feedback="Clean work — add a reset button next time.", submitted_at="2026-06-02", graded_by="Suresh Rao"),
            SubmissionDB(assignment_id=2, student_id="STU-001", student_name="Ravi Kumar", content="Todo app done.", link="https://github.com/ravi/todo", status="Submitted", submitted_at="2026-06-03"),
            # Aisha (React) — graded
            SubmissionDB(assignment_id=1, student_id="STU-004", student_name="Aisha Khan", content="Counter component with +/- buttons.", link="", status="Graded", marks=92, feedback="Excellent, well structured.", submitted_at="2026-06-01", graded_by="Suresh Rao"),
            # Meera (Python) — graded
            SubmissionDB(assignment_id=4, student_id="STU-002", student_name="Meera Nair", content="FizzBuzz + helpers attached.", link="", status="Graded", marks=95, feedback="Great use of functions.", submitted_at="2026-05-30", graded_by="Priya Menon"),
            # John (Java) — pending review
            SubmissionDB(assignment_id=3, student_id="STU-003", student_name="John Mathew", content="Book CRUD controller implemented.", link="https://github.com/john/book-api", status="Submitted", submitted_at="2026-06-03"),
        ])

        # --- online classes (real Google Meet link) ---
        # https://meet.google.com/new opens Google Meet and starts a real
        # meeting on click (when signed into a Google account).
        session.add_all([
            ClassSessionDB(course="React Fundamentals", title="Live: State & Hooks Q&A", scheduled_at="2026-06-10 10:00", meet_link="https://meet.google.com/new", created_by="Suresh Rao"),
            ClassSessionDB(course="Java Backend",       title="Live: Spring Data JPA",   scheduled_at="2026-06-11 14:00", meet_link="https://meet.google.com/new", created_by="Anita Sharma"),
            ClassSessionDB(course="Python Basics",      title="Live: Recap & Exam Prep", scheduled_at="2026-06-09 09:00", meet_link="https://meet.google.com/new", created_by="Priya Menon"),
        ])

        # --- per-student attendance across a few dates ---
        # P = present, A = absent. Each character is one class date.
        roster = {
            "React Fundamentals": [("STU-001", "Ravi Kumar"), ("STU-004", "Aisha Khan")],
            "Java Backend":       [("STU-003", "John Mathew"), ("STU-005", "David Lee")],
            "Python Basics":      [("STU-002", "Meera Nair")],
        }
        dates = ["2026-05-26", "2026-05-28", "2026-06-01", "2026-06-03"]
        pattern = {  # attendance per student over the 4 dates
            "STU-001": "PPPA", "STU-004": "PPPP",
            "STU-003": "PAPA", "STU-005": "PPAP",
            "STU-002": "PPPP",
        }
        marker = {"React Fundamentals": "Suresh Rao", "Java Backend": "Anita Sharma", "Python Basics": "Priya Menon"}
        for course, people in roster.items():
            for sid, sname in people:
                for d, flag in zip(dates, pattern[sid]):
                    session.add_all([AttendanceDB(
                        student_id=sid, student_name=sname, course=course, date=d,
                        status="Present" if flag == "P" else "Absent",
                        marked_by=marker[course],
                    )])

        session.commit()


def next_id(session, model, prefix):
    # Generate the next ID like STU-006 based on current row count.
    count = len(session.exec(select(model)).all())
    return f"{prefix}-{str(count + 1).zfill(3)}"
