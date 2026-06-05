# routers/classes.py — online classes (Google Meet links).
#   • Trainers/admins SCHEDULE a class (paste a Meet link).
#   • Students SEE the classes for their course and click "Join".
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import ClassSessionDB, ClassIn, StudentDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/classes", tags=["Classes"])


@router.get("", response_model=list[ClassSessionDB])
def list_classes(session: Session = Depends(get_session), user=Depends(get_current_user)):
    rows = session.exec(select(ClassSessionDB)).all()
    if user.role == "student" and user.ref_id:
        me = session.get(StudentDB, user.ref_id)
        if me:
            rows = [c for c in rows if c.course == me.course]
    elif user.role == "trainer":
        rows = [c for c in rows if c.created_by == user.name]
    return rows


@router.post("", response_model=ClassSessionDB, status_code=201)
def schedule_class(body: ClassIn, session: Session = Depends(get_session),
                   user=Depends(require_role("admin", "trainer"))):
    session_row = ClassSessionDB(**body.model_dump(), created_by=user.name)
    session.add(session_row); session.commit(); session.refresh(session_row)
    return session_row


@router.delete("/{class_id}")
def delete_class(class_id: int, session: Session = Depends(get_session),
                 user=Depends(require_role("admin", "trainer"))):
    cls = session.get(ClassSessionDB, class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    session.delete(cls); session.commit()
    return {"deleted": class_id}
