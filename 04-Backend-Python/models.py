# =====================================================================
# models.py  —  the "shapes" of our data (Pydantic models)
#
# BUSINESS LEVEL: These are the official forms. Just like a paper form has
#   named blanks ("Name: ___", "Email: ___"), each model below defines what
#   fields a Student / Trainer / Course must have. The server rejects anything
#   that doesn't fit the form — automatic quality control.
#
# CODE LEVEL: Pydantic models give us automatic request validation and shape
#   the JSON responses. FastAPI also turns them into the interactive /docs.
# =====================================================================
from pydantic import BaseModel, EmailStr
from typing import Optional


# ---- Authentication ----
class Token(BaseModel):
    access_token: str          # the JWT "access pass" string
    token_type: str = "bearer"
    role: str                  # admin / trainer / student
    name: str


class UserOut(BaseModel):
    username: str
    name: str
    role: str


# ---- Students ----
class StudentIn(BaseModel):            # what you send to CREATE/UPDATE
    name: str
    email: str
    course: str
    status: str = "Active"

class Student(StudentIn):              # what you GET back (adds the id)
    id: str


# ---- Trainers ----
class TrainerIn(BaseModel):
    name: str
    expertise: str
    courses: str

class Trainer(TrainerIn):
    id: str


# ---- Courses ----
class CourseIn(BaseModel):
    name: str
    trainer: str
    duration: str
    status: str = "Upcoming"

class Course(CourseIn):
    id: str


# ---- Attendance ----
class AttendanceIn(BaseModel):
    course: str
    date: str
    present: list[str]         # list of student IDs marked present


# ---- Certificates ----
class Certificate(BaseModel):
    student: str
    course: str
    status: str
