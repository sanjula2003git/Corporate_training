# routers/submissions.py — grading + a student's own submission history.
#   • Trainers/admins GRADE a submission (marks out of max + feedback).
#   • Students LIST their own submissions (with the assignment title).
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import SubmissionDB, GradeIn, AssignmentDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.get("/me")
def my_submissions(session: Session = Depends(get_session), user=Depends(get_current_user)):
    if not user.ref_id:
        return []
    subs = session.exec(
        select(SubmissionDB).where(SubmissionDB.student_id == user.ref_id)
    ).all()
    out = []
    for s in subs:
        a = session.get(AssignmentDB, s.assignment_id)
        out.append({**s.model_dump(),
                    "assignment_title": a.title if a else "(removed)",
                    "max_marks": a.max_marks if a else 100})
    return out


@router.put("/{submission_id}/grade", response_model=SubmissionDB)
def grade_submission(submission_id: int, body: GradeIn,
                     session: Session = Depends(get_session),
                     user=Depends(require_role("admin", "trainer"))):
    sub = session.get(SubmissionDB, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    assignment = session.get(AssignmentDB, sub.assignment_id)
    max_marks = assignment.max_marks if assignment else 100
    if body.marks < 0 or body.marks > max_marks:
        raise HTTPException(status_code=400, detail=f"Marks must be between 0 and {max_marks}.")
    sub.marks = body.marks
    sub.feedback = body.feedback
    sub.status = "Graded"
    sub.graded_by = user.name
    session.add(sub); session.commit(); session.refresh(sub)
    return sub
