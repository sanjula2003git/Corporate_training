# routers/courses.py — /api/courses endpoints (CRUD). Admin-managed.
from fastapi import APIRouter, Depends, HTTPException
import data
from models import Course, CourseIn
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=list[Course])
def list_courses(user=Depends(get_current_user)):
    return data.courses


@router.post("", response_model=Course, status_code=201)
def add_course(body: CourseIn, user=Depends(require_role("admin"))):
    new = {"id": data.next_id(data.courses, "CRS"), **body.model_dump()}
    data.courses.append(new)
    return new


@router.put("/{course_id}", response_model=Course)
def update_course(course_id: str, body: CourseIn, user=Depends(require_role("admin"))):
    for c in data.courses:
        if c["id"] == course_id:
            c.update(body.model_dump())
            return c
    raise HTTPException(status_code=404, detail="Course not found")


@router.delete("/{course_id}")
def delete_course(course_id: str, user=Depends(require_role("admin"))):
    before = len(data.courses)
    data.courses[:] = [c for c in data.courses if c["id"] != course_id]
    if len(data.courses) == before:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"deleted": course_id}
