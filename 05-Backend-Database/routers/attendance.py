# routers/attendance.py — PER-STUDENT attendance saved into the database.
# Marking attendance for a class writes one row per enrolled student
# (Present/Absent), so each student can later see their own attendance % and
# admins can audit everyone.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import AttendanceDB, AttendanceIn, StudentDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("", response_model=list[AttendanceDB])
def list_attendance(session: Session = Depends(get_session),
                    user=Depends(require_role("admin", "trainer"))):
    return session.exec(select(AttendanceDB)).all()


@router.get("/me", response_model=list[AttendanceDB])
def my_attendance(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """A student's own attendance rows (used by the student dashboard/progress)."""
    if not user.ref_id:
        return []
    return session.exec(
        select(AttendanceDB).where(AttendanceDB.student_id == user.ref_id)
    ).all()


@router.post("", status_code=201)
def save_attendance(body: AttendanceIn, session: Session = Depends(get_session),
                    user=Depends(require_role("admin", "trainer"))):
    # Roster = everyone enrolled in that course. Students in `present` are
    # marked Present; the rest of the roster is marked Absent.
    roster = session.exec(select(StudentDB).where(StudentDB.course == body.course)).all()
    if not roster:
        raise HTTPException(status_code=404, detail="No students enrolled in that course.")
    present = set(body.present)
    saved = 0
    for s in roster:
        session.add(AttendanceDB(
            student_id=s.id, student_name=s.name, course=body.course, date=body.date,
            status="Present" if s.id in present else "Absent", marked_by=user.name,
        ))
        saved += 1
    session.commit()
    return {"saved": saved, "present_count": len(present & {s.id for s in roster}),
            "course": body.course, "date": body.date}
