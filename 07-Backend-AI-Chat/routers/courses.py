# routers/courses.py — Course CRUD backed by the database.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session, next_id
from models import CourseDB, CourseIn
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=list[CourseDB])
def list_courses(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(CourseDB)).all()


@router.post("", response_model=CourseDB, status_code=201)
def add_course(body: CourseIn, session: Session = Depends(get_session),
               user=Depends(require_role("admin"))):
    course = CourseDB(id=next_id(session, CourseDB, "CRS"), **body.model_dump())
    session.add(course); session.commit(); session.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseDB)
def update_course(course_id: str, body: CourseIn, session: Session = Depends(get_session),
                  user=Depends(require_role("admin"))):
    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in body.model_dump().items():
        setattr(course, key, value)
    session.add(course); session.commit(); session.refresh(course)
    return course


@router.delete("/{course_id}")
def delete_course(course_id: str, session: Session = Depends(get_session),
                  user=Depends(require_role("admin"))):
    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    session.delete(course); session.commit()
    return {"deleted": course_id}
