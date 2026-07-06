# =====================================================================
# models.py  —  DATABASE TABLES + input shapes (SQLModel)
#
# BUSINESS LEVEL: Each class with `table=True` is a real TABLE in the database
#   (like a labeled drawer in a filing cabinet, with columns for each field).
#   The "...In" classes are the blank forms you fill to add/edit a record.
#
# CODE LEVEL: SQLModel = SQLAlchemy (database) + Pydantic (validation) in one.
#   One class defines both the DB table AND the API data shape.
#
# This stage adds ROLE-BASED features: course materials, assignments,
# submissions + marks, online classes (Google Meet links), and per-student
# attendance — so students, trainers and admins each get their own portal.
# =====================================================================
from sqlmodel import SQLModel, Field
from typing import Optional


# ---------- TABLES (stored in the database) ----------
class UserDB(SQLModel, table=True):
    __tablename__ = "users"
    username: str = Field(primary_key=True)   # primary key = unique drawer label
    name: str
    role: str                                  # admin / trainer / student
    password_hash: str                         # bcrypt hash (never plain text)
    # Links a login to its student/trainer record (e.g. "STU-001" / "TRN-002").
    # Pure admins have no linked record, so this stays empty.
    ref_id: Optional[str] = None


# =====================================================================
# ⚡ PERFORMANCE — DATABASE INDEXING  (index=True below)
#
# BUSINESS LEVEL: An index is like the index at the back of a textbook. Without
#   it, to find "all students taking React" the database must read EVERY row
#   (a "full table scan"). With an index on that column, it jumps straight to
#   the matching rows — much faster once you have thousands of records.
#
# CODE LEVEL: `Field(index=True)` tells the database to build & maintain a
#   sorted lookup structure (a B-tree) for that column. We index the columns we
#   actually SEARCH or FILTER by (name, email, course, student_id, ...).
#   Trade-off: indexes speed up reads but slightly slow writes and use disk —
#   so you index searched columns, not every column.
# =====================================================================
class StudentDB(SQLModel, table=True):
    __tablename__ = "students"
    id: str = Field(primary_key=True)             # primary keys are auto-indexed
    name: str = Field(index=True)                 # we search students by name
    email: str = Field(index=True)                # ...and by email
    course: str = Field(index=True)               # ...and filter by course
    status: str = "Active"


class TrainerDB(SQLModel, table=True):
    __tablename__ = "trainers"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)                 # searched by name
    expertise: str
    courses: str


class CourseDB(SQLModel, table=True):
    __tablename__ = "courses"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)                 # searched by name
    trainer: str
    duration: str
    status: str = "Upcoming"


class CertificateDB(SQLModel, table=True):
    __tablename__ = "certificates"
    id: Optional[int] = Field(default=None, primary_key=True)  # auto-numbered
    student: str
    course: str
    status: str


# ---- Per-student attendance: one row = one student on one date for a course.
# (The old version stored only a head-count; per-student rows let each student
#  see THEIR OWN attendance % and let admins audit everyone.)
class AttendanceDB(SQLModel, table=True):
    __tablename__ = "attendance"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)    # each student looks up THEIR own rows
    student_name: str
    course: str = Field(index=True)        # admins filter attendance by course
    date: str
    status: str            # "Present" / "Absent"
    marked_by: str


# ---- Course materials a trainer shares and students read.
class MaterialDB(SQLModel, table=True):
    __tablename__ = "materials"
    id: Optional[int] = Field(default=None, primary_key=True)
    course: str
    title: str
    kind: str = "Document"   # Document / Video / Link
    url: str = ""
    description: str = ""
    uploaded_by: str = ""


# ---- An assignment a trainer gives to a course.
class AssignmentDB(SQLModel, table=True):
    __tablename__ = "assignments"
    id: Optional[int] = Field(default=None, primary_key=True)
    course: str
    title: str
    description: str = ""
    due_date: str = ""
    max_marks: int = 100
    created_by: str = ""


# ---- A student's submission for an assignment (+ the trainer's marks).
class SubmissionDB(SQLModel, table=True):
    __tablename__ = "submissions"
    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(index=True)   # "show all submissions for this assignment"
    student_id: str = Field(index=True)      # "show all of this student's submissions"
    student_name: str
    content: str = ""          # the student's typed answer
    link: str = ""             # optional link (e.g. GitHub / Google Doc)
    status: str = "Submitted"  # Submitted / Graded
    marks: Optional[int] = None
    feedback: str = ""
    submitted_at: str = ""
    graded_by: str = ""


# ---- Support chat: a 1-on-1 thread between a student/trainer and the admins.
# Every message belongs to ONE thread, identified by the non-admin user's
# username (thread_user). The student/trainer and any admin both post into it.
class ChatMessageDB(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_user: str           # username of the student/trainer who owns the thread
    sender_username: str
    sender_name: str
    sender_role: str           # student / trainer / admin
    message: str
    created_at: str = ""


# ---- A scheduled online class (the trainer pastes a Google Meet link).
class ClassSessionDB(SQLModel, table=True):
    __tablename__ = "class_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    course: str
    title: str
    scheduled_at: str = ""     # e.g. "2026-06-10 10:00"
    meet_link: str = ""
    created_by: str = ""


# ---------- INPUT FORMS (not stored directly; used to validate requests) ----------
class StudentIn(SQLModel):
    name: str
    email: str
    course: str
    status: str = "Active"

class TrainerIn(SQLModel):
    name: str
    expertise: str
    courses: str

class CourseIn(SQLModel):
    name: str
    trainer: str
    duration: str
    status: str = "Upcoming"

class AdminIn(SQLModel):
    name: str
    username: str
    password: str

class MaterialIn(SQLModel):
    course: str
    title: str
    kind: str = "Document"
    url: str = ""
    description: str = ""

class AssignmentIn(SQLModel):
    course: str
    title: str
    description: str = ""
    due_date: str = ""
    max_marks: int = 100

class SubmissionIn(SQLModel):
    content: str = ""
    link: str = ""

class GradeIn(SQLModel):
    marks: int
    feedback: str = ""

class ClassIn(SQLModel):
    course: str
    title: str
    scheduled_at: str = ""
    meet_link: str = ""

class AttendanceIn(SQLModel):
    course: str
    date: str
    present: list[str]     # ids of students marked present; the rest are Absent

class ChatIn(SQLModel):
    message: str
    # Only used when an ADMIN replies — which student/trainer thread to post to.
    # A student/trainer leaves this empty (it defaults to their own thread).
    to_user: Optional[str] = None
