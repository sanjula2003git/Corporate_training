# routers/students.py — Student CRUD backed by the DATABASE.
# Only ADMINS may add/update/delete students (trainers & students cannot).
# Adding a student also auto-creates their LOGIN account, so the new student
# can immediately sign in and see their own dashboard.
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session, next_id
from models import StudentDB, StudentIn, UserDB
from auth import get_current_user, require_role, create_user_account

router = APIRouter(prefix="/api/students", tags=["Students"])


# ---------------------------------------------------------------------
# ⚡ PERFORMANCE — ASYNCHRONOUS PROCESSING (background task)
#
# BUSINESS LEVEL: When you add a student we also want to "email" them their
#   login. Sending an email is SLOW (talking to a mail server). We should NOT
#   make the admin wait for that — the screen should say "done" instantly while
#   the email goes out in the background.
#
# CODE LEVEL: FastAPI's BackgroundTasks runs this function AFTER the response
#   has been sent. The HTTP request returns immediately; this runs afterwards.
#   (time.sleep here simulates the slow email/network call.)
# ---------------------------------------------------------------------
def send_welcome_email(name: str, username: str):
    time.sleep(2)                      # pretend an email server takes 2 seconds
    print(f"[background] Welcome email sent to {name} (login: {username})")


@router.get("", response_model=list[StudentDB])
def list_students(
    q: str | None = None,      # optional search text (uses the INDEXED name column)
    limit: int = 50,           # ⚡ QUERY OPTIMIZATION: page size — max rows to return
    offset: int = 0,           # ⚡ how many rows to skip (which "page" you're on)
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    # ⚡ PERFORMANCE — QUERY OPTIMIZATION
    # Instead of "SELECT * FROM students" (return EVERYTHING every time), we:
    #   1) optionally FILTER by name — fast because `name` is indexed (see models.py)
    #   2) LIMIT/OFFSET so we fetch only ONE PAGE, not all 10,000 rows.
    # This keeps the query fast and the response small no matter how big the DB grows.
    query = select(StudentDB)
    if q:
        query = query.where(StudentDB.name.contains(q))   # index-backed lookup
    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.post("", status_code=201)
def add_student(body: StudentIn, background_tasks: BackgroundTasks,
                session: Session = Depends(get_session),
                user=Depends(require_role("admin"))):
    student = StudentDB(id=next_id(session, StudentDB, "STU"), **body.model_dump())
    session.add(student)                                   # INSERT student
    # Auto-create a login for this student (default password: student123).
    account = create_user_account(session, name=student.name, role="student",
                                  password="student123", ref_id=student.id)
    session.commit()
    session.refresh(student)
    # ⚡ Queue the slow "email" to run AFTER we respond — the admin doesn't wait.
    background_tasks.add_task(send_welcome_email, student.name, account.username)
    return {"student": student, "login": {"username": account.username, "password": "student123"}}


@router.put("/{student_id}", response_model=StudentDB)
def update_student(student_id: str, body: StudentIn, session: Session = Depends(get_session),
                   user=Depends(require_role("admin"))):
    student = session.get(StudentDB, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in body.model_dump().items():
        setattr(student, key, value)
    session.add(student); session.commit(); session.refresh(student)  # UPDATE
    return student


@router.delete("/{student_id}")
def delete_student(student_id: str, session: Session = Depends(get_session),
                   user=Depends(require_role("admin"))):
    student = session.get(StudentDB, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Remove the linked login account too, if any.
    account = session.exec(select(UserDB).where(UserDB.ref_id == student_id)).first()
    if account:
        session.delete(account)
    session.delete(student); session.commit()             # DELETE
    return {"deleted": student_id}
