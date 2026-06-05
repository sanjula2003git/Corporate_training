# routers/dashboards.py — the three ROLE dashboards.
#   • /api/dashboard/student  → one student's own progress
#   • /api/dashboard/trainer  → a trainer's students + assignments overview
#   • /api/dashboard/admin    → whole-org view (every student/trainer/course)
#
# All numbers are computed live from the database (attendance rows, submissions,
# assignments), so the dashboards always reflect reality.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (StudentDB, TrainerDB, CourseDB, AttendanceDB,
                    AssignmentDB, SubmissionDB, ClassSessionDB)
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboards"])


def pct(part, whole):
    return round(part / whole * 100) if whole else 0


def attendance_pct(session, student_id):
    rows = session.exec(select(AttendanceDB).where(AttendanceDB.student_id == student_id)).all()
    present = sum(1 for r in rows if r.status == "Present")
    return pct(present, len(rows)), present, len(rows)


def student_summary(session, student):
    """Reusable per-student progress block (used by all three dashboards)."""
    att_pct, present, total = attendance_pct(session, student.id)
    assignments = session.exec(select(AssignmentDB).where(AssignmentDB.course == student.course)).all()
    subs = session.exec(select(SubmissionDB).where(SubmissionDB.student_id == student.id)).all()
    graded = [s for s in subs if s.status == "Graded" and s.marks is not None]
    avg_marks = round(sum(s.marks for s in graded) / len(graded)) if graded else None
    return {
        "id": student.id, "name": student.name, "course": student.course,
        "status": student.status,
        "attendancePct": att_pct, "present": present, "totalClasses": total,
        "assignmentsTotal": len(assignments),
        "submitted": len(subs), "graded": len(graded),
        "assignmentPct": pct(len(subs), len(assignments)),
        "avgMarks": avg_marks,
    }


# ---------------- STUDENT ----------------
@router.get("/student")
def student_dashboard(session: Session = Depends(get_session), user=Depends(require_role("student"))):
    me = session.get(StudentDB, user.ref_id) if user.ref_id else None
    if not me:
        raise HTTPException(status_code=404, detail="No student record linked to this login.")
    summary = student_summary(session, me)

    assignments = session.exec(select(AssignmentDB).where(AssignmentDB.course == me.course)).all()
    rows = []
    for a in assignments:
        sub = session.exec(
            select(SubmissionDB).where(SubmissionDB.assignment_id == a.id,
                                       SubmissionDB.student_id == me.id)
        ).first()
        rows.append({"id": a.id, "title": a.title, "due_date": a.due_date,
                     "max_marks": a.max_marks,
                     "status": sub.status if sub else "Pending",
                     "marks": sub.marks if sub else None,
                     "feedback": sub.feedback if sub else ""})

    upcoming = session.exec(select(ClassSessionDB).where(ClassSessionDB.course == me.course)).all()
    return {
        "name": me.name, "course": me.course,
        "attendancePct": summary["attendancePct"],
        "present": summary["present"], "totalClasses": summary["totalClasses"],
        "assignmentPct": summary["assignmentPct"],
        "submitted": summary["submitted"], "assignmentsTotal": summary["assignmentsTotal"],
        "avgMarks": summary["avgMarks"],
        "pendingAssignments": sum(1 for r in rows if r["status"] == "Pending"),
        "assignments": rows,
        "upcomingClasses": [{"title": c.title, "scheduled_at": c.scheduled_at, "meet_link": c.meet_link} for c in upcoming],
    }


# ---------------- TRAINER ----------------
@router.get("/trainer")
def trainer_dashboard(session: Session = Depends(get_session), user=Depends(require_role("trainer"))):
    # Courses this trainer teaches.
    my_courses = [c.name for c in session.exec(select(CourseDB).where(CourseDB.trainer == user.name)).all()]
    students = [s for s in session.exec(select(StudentDB)).all() if s.course in my_courses]
    student_rows = [student_summary(session, s) for s in students]

    my_assignments = session.exec(select(AssignmentDB).where(AssignmentDB.created_by == user.name)).all()
    assignment_rows, pending_reviews = [], 0
    for a in my_assignments:
        subs = session.exec(select(SubmissionDB).where(SubmissionDB.assignment_id == a.id)).all()
        ungraded = sum(1 for s in subs if s.status != "Graded")
        pending_reviews += ungraded
        assignment_rows.append({"id": a.id, "title": a.title, "course": a.course,
                                "due_date": a.due_date, "submissions": len(subs),
                                "graded": len(subs) - ungraded, "pending": ungraded})

    avg = [r["attendancePct"] for r in student_rows]
    return {
        "name": user.name,
        "courses": my_courses,
        "totalStudents": len(students),
        "avgAttendance": round(sum(avg) / len(avg)) if avg else 0,
        "pendingReviews": pending_reviews,
        "students": student_rows,
        "assignments": assignment_rows,
    }


# ---------------- ADMIN ----------------
@router.get("/admin")
def admin_dashboard(session: Session = Depends(get_session), user=Depends(require_role("admin"))):
    students = session.exec(select(StudentDB)).all()
    trainers = session.exec(select(TrainerDB)).all()
    courses = session.exec(select(CourseDB)).all()
    classes = session.exec(select(ClassSessionDB)).all()

    student_rows = [student_summary(session, s) for s in students]
    all_att = [r["attendancePct"] for r in student_rows]

    # Per-course progress block.
    course_rows = []
    for c in courses:
        in_course = [r for r in student_rows if r["course"] == c.name]
        att = [r["attendancePct"] for r in in_course]
        marks = [r["avgMarks"] for r in in_course if r["avgMarks"] is not None]
        course_rows.append({
            "course": c.name, "trainer": c.trainer, "status": c.status,
            "enrolled": len(in_course),
            "avgAttendance": round(sum(att) / len(att)) if att else 0,
            "avgMarks": round(sum(marks) / len(marks)) if marks else None,
        })

    pending_reviews = sum(1 for s in session.exec(select(SubmissionDB)).all() if s.status != "Graded")

    return {
        "totalStudents": len(students),
        "totalTrainers": len(trainers),
        "totalCourses": len(courses),
        "totalClasses": len(classes),
        "avgAttendance": round(sum(all_att) / len(all_att)) if all_att else 0,
        "pendingReviews": pending_reviews,
        "students": student_rows,
        "trainers": [{"id": t.id, "name": t.name, "expertise": t.expertise, "courses": t.courses} for t in trainers],
        "courses": course_rows,
    }
