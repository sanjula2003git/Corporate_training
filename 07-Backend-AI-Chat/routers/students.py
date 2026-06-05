# routers/students.py — Student CRUD backed by the DATABASE.
# Only ADMINS may add/update/delete students (trainers & students cannot).
# Adding a student also auto-creates their LOGIN account, so the new student
# can immediately sign in and see their own dashboard.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session, next_id
from models import StudentDB, StudentIn, UserDB
from auth import get_current_user, require_role, create_user_account

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=list[StudentDB])
def list_students(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(StudentDB)).all()          # SELECT * FROM students


@router.post("", status_code=201)
def add_student(body: StudentIn, session: Session = Depends(get_session),
                user=Depends(require_role("admin"))):
    student = StudentDB(id=next_id(session, StudentDB, "STU"), **body.model_dump())
    session.add(student)                                   # INSERT student
    # Auto-create a login for this student (default password: student123).
    account = create_user_account(session, name=student.name, role="student",
                                  password="student123", ref_id=student.id)
    session.commit()
    session.refresh(student)
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
