# routers/assignments.py — assignments + student submissions.
#   • Trainers/admins CREATE assignments and SEE every student's submission.
#   • Students SEE the assignments for their course and SUBMIT their work.
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (AssignmentDB, AssignmentIn, SubmissionDB, SubmissionIn,
                    StudentDB)
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


@router.get("")
def list_assignments(session: Session = Depends(get_session), user=Depends(get_current_user)):
    """Role-aware list:
       • student → assignments for their course + THEIR submission status
       • trainer → assignments they created + submission counts
       • admin   → all assignments + submission counts
    """
    assignments = session.exec(select(AssignmentDB)).all()

    if user.role == "student":
        me = session.get(StudentDB, user.ref_id) if user.ref_id else None
        course = me.course if me else None
        out = []
        for a in assignments:
            if a.course != course:
                continue
            sub = session.exec(
                select(SubmissionDB).where(SubmissionDB.assignment_id == a.id,
                                           SubmissionDB.student_id == user.ref_id)
            ).first()
            out.append({**a.model_dump(),
                        "submission_status": sub.status if sub else "Pending",
                        "my_marks": sub.marks if sub else None,
                        "my_feedback": sub.feedback if sub else "",
                        "my_content": sub.content if sub else "",
                        "my_link": sub.link if sub else ""})
        return out

    # trainer sees their own; admin sees all
    if user.role == "trainer":
        assignments = [a for a in assignments if a.created_by == user.name]

    out = []
    for a in assignments:
        subs = session.exec(select(SubmissionDB).where(SubmissionDB.assignment_id == a.id)).all()
        graded = sum(1 for s in subs if s.status == "Graded")
        out.append({**a.model_dump(),
                    "submission_count": len(subs),
                    "graded_count": graded,
                    "pending": len(subs) - graded})
    return out


@router.post("", response_model=AssignmentDB, status_code=201)
def create_assignment(body: AssignmentIn, session: Session = Depends(get_session),
                      user=Depends(require_role("admin", "trainer"))):
    assignment = AssignmentDB(**body.model_dump(), created_by=user.name)
    session.add(assignment); session.commit(); session.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, session: Session = Depends(get_session),
                      user=Depends(require_role("admin", "trainer"))):
    assignment = session.get(AssignmentDB, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    # Remove its submissions too.
    for s in session.exec(select(SubmissionDB).where(SubmissionDB.assignment_id == assignment_id)).all():
        session.delete(s)
    session.delete(assignment); session.commit()
    return {"deleted": assignment_id}


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionDB])
def list_submissions(assignment_id: int, session: Session = Depends(get_session),
                     user=Depends(require_role("admin", "trainer"))):
    """Every student's submission for one assignment (shown separately per
    student, so the trainer can review and grade each one)."""
    return session.exec(
        select(SubmissionDB).where(SubmissionDB.assignment_id == assignment_id)
    ).all()


@router.post("/{assignment_id}/submit", status_code=201)
def submit_assignment(assignment_id: int, body: SubmissionIn,
                      session: Session = Depends(get_session),
                      user=Depends(require_role("student"))):
    assignment = session.get(AssignmentDB, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    me = session.get(StudentDB, user.ref_id) if user.ref_id else None
    if not me:
        raise HTTPException(status_code=400, detail="No student record linked to this login.")
    if me.course != assignment.course:
        raise HTTPException(status_code=403, detail="This assignment is not for your course.")

    # One submission per student per assignment — update if it already exists.
    sub = session.exec(
        select(SubmissionDB).where(SubmissionDB.assignment_id == assignment_id,
                                   SubmissionDB.student_id == user.ref_id)
    ).first()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if sub:
        sub.content, sub.link, sub.status = body.content, body.link, "Submitted"
        sub.marks, sub.feedback, sub.graded_by = None, "", ""
        sub.submitted_at = today
    else:
        sub = SubmissionDB(assignment_id=assignment_id, student_id=me.id,
                           student_name=me.name, content=body.content, link=body.link,
                           status="Submitted", submitted_at=today)
    session.add(sub); session.commit(); session.refresh(sub)
    return {"submitted": True, "assignment": assignment.title}
