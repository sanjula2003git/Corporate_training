# routers/attendance.py — /api/attendance. Admin & Trainer can mark attendance.
from fastapi import APIRouter, Depends
import data
from models import AttendanceIn
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("")
def list_attendance(user=Depends(get_current_user)):
    return data.attendance_records


@router.post("", status_code=201)
def save_attendance(body: AttendanceIn, user=Depends(require_role("admin", "trainer"))):
    # BUSINESS: record who was present in a class on a given date.
    record = body.model_dump()
    record["marked_by"] = user["name"]
    data.attendance_records.append(record)
    return {"saved": True, "present_count": len(body.present), "course": body.course}
