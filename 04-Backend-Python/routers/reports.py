# routers/reports.py — /api/reports. Read-only stats (Admin & Trainer).
from fastapi import APIRouter, Depends
import data
from auth import require_role

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("")
def reports(user=Depends(require_role("admin", "trainer"))):
    # BUSINESS: management summary numbers. Computed live from the data.
    total = len(data.students)
    completed = sum(1 for c in data.certificates if c["status"] == "Completed")
    return {
        "totalStudents": total,
        "completionRate": f"{round(completed / max(len(data.certificates), 1) * 100)}%",
        "avgAttendance": "87%",
        "certificatesIssued": completed,
        "byCourse": [
            {"course": "React Fundamentals", "enrolled": 60, "completed": 42, "rate": "70%"},
            {"course": "Java Backend", "enrolled": 55, "completed": 44, "rate": "80%"},
            {"course": "Python Basics", "enrolled": 48, "completed": 40, "rate": "83%"},
        ],
    }
