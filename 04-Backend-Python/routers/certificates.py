# routers/certificates.py — /api/certificates. Generate only for Completed courses.
from fastapi import APIRouter, Depends, HTTPException
import data
from models import Certificate
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get("", response_model=list[Certificate])
def list_certificates(user=Depends(get_current_user)):
    return data.certificates


@router.post("/generate")
def generate_certificate(student: str, course: str,
                         user=Depends(require_role("admin", "trainer"))):
    # BUSINESS: you can only issue a certificate if the course is completed.
    for c in data.certificates:
        if c["student"] == student and c["course"] == course:
            if c["status"] != "Completed":
                raise HTTPException(status_code=400,
                    detail="Cannot generate — course not completed.")
            return {"generated": True, "student": student, "course": course,
                    "message": f"Certificate generated for {student} — {course}"}
    raise HTTPException(status_code=404, detail="Record not found")
