# routers/students.py — all /api/students endpoints (CRUD)
#
# BUSINESS: the "Students" filing drawer. Anyone logged in can read it,
#   but only Admin/Trainer can add or edit, and only Admin can delete.
# CODE: each function = one REST endpoint. The `Depends(require_role(...))`
#   line is the security guard on that endpoint.
from fastapi import APIRouter, Depends, HTTPException
import data
from models import Student, StudentIn
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=list[Student])
def list_students(user=Depends(get_current_user)):
    # Any logged-in role may view the list.
    return data.students


@router.post("", response_model=Student, status_code=201)
def add_student(body: StudentIn, user=Depends(require_role("admin", "trainer"))):
    new = {"id": data.next_id(data.students, "STU"), **body.model_dump()}
    data.students.append(new)
    return new


@router.put("/{student_id}", response_model=Student)
def update_student(student_id: str, body: StudentIn,
                   user=Depends(require_role("admin", "trainer"))):
    for s in data.students:
        if s["id"] == student_id:
            s.update(body.model_dump())
            return s
    raise HTTPException(status_code=404, detail="Student not found")


@router.delete("/{student_id}")
def delete_student(student_id: str, user=Depends(require_role("admin"))):
    # Only Admin may delete — demonstrates role-based authorization.
    before = len(data.students)
    data.students[:] = [s for s in data.students if s["id"] != student_id]
    if len(data.students) == before:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"deleted": student_id}
