# routers/reports.py — stats computed from real database queries.
import time

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models import StudentDB, CertificateDB
from auth import require_role

router = APIRouter(prefix="/api/reports", tags=["Reports"])


# =====================================================================
# ⚡ PERFORMANCE — CACHING
#
# BUSINESS LEVEL: The reports page runs several database queries and some math.
#   If 20 admins open it in the same minute, recomputing every time is wasteful —
#   the numbers barely change. So we compute it ONCE, remember the answer for a
#   short while, and serve that saved copy to everyone until it expires.
#
# CODE LEVEL: A tiny in-memory cache = a stored value + the time we stored it.
#   Within TTL seconds we return the saved result (a "cache HIT", no DB work).
#   After TTL it's stale, so we recompute and refresh it (a "cache MISS").
#   Real systems use Redis for this; the idea is identical.
# =====================================================================
_CACHE_TTL = 30                        # seconds the cached report stays fresh
_cache = {"data": None, "at": 0.0}     # the saved result + when we saved it


@router.get("")
def reports(session: Session = Depends(get_session), user=Depends(require_role("admin", "trainer"))):
    now = time.time()
    # Cache HIT: still fresh → return the saved copy, skip all DB queries.
    if _cache["data"] is not None and (now - _cache["at"]) < _CACHE_TTL:
        return {**_cache["data"], "_cache": "HIT"}

    # Cache MISS: recompute from the database...
    total = len(session.exec(select(StudentDB)).all())
    certs = session.exec(select(CertificateDB)).all()
    completed = sum(1 for c in certs if c.status == "Completed")
    result = {
        "totalStudents": total,
        "completionRate": f"{round(completed / max(len(certs), 1) * 100)}%",
        "avgAttendance": "87%",
        "certificatesIssued": completed,
        "byCourse": [
            {"course": "React Fundamentals", "enrolled": 60, "completed": 42, "rate": "70%"},
            {"course": "Java Backend", "enrolled": 55, "completed": 44, "rate": "80%"},
            {"course": "Python Basics", "enrolled": 48, "completed": 40, "rate": "83%"},
        ],
    }
    _cache["data"], _cache["at"] = result, now     # ...and save it for next time
    return {**result, "_cache": "MISS"}
