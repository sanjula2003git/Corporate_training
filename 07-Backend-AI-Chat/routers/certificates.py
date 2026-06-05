# routers/certificates.py — certificates read from / checked against the database.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import CertificateDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get("", response_model=list[CertificateDB])
def list_certificates(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(CertificateDB)).all()


@router.post("/generate")
def generate_certificate(student: str, course: str, session: Session = Depends(get_session),
                         user=Depends(require_role("admin", "trainer"))):
    cert = session.exec(
        select(CertificateDB).where(CertificateDB.student == student,
                                    CertificateDB.course == course)
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Record not found")
    if cert.status != "Completed":
        raise HTTPException(status_code=400, detail="Cannot generate — course not completed.")
    return {"generated": True, "student": student, "course": course,
            "message": f"Certificate generated for {student} — {course}"}
