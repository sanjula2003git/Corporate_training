# routers/admins.py — managing admin logins (admin-only).
# The brief: an admin can add ANOTHER admin, who then has the same powers
# (add courses/students/trainers, see the global dashboard).
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import UserDB, AdminIn
from auth import require_role, hash_password

router = APIRouter(prefix="/api", tags=["Admins"])


@router.get("/users")
def list_users(session: Session = Depends(get_session), user=Depends(require_role("admin"))):
    """All logins (admins/trainers/students) — never returns password hashes."""
    users = session.exec(select(UserDB)).all()
    return [{"username": u.username, "name": u.name, "role": u.role, "ref_id": u.ref_id}
            for u in users]


@router.post("/admins", status_code=201)
def add_admin(body: AdminIn, session: Session = Depends(get_session),
              user=Depends(require_role("admin"))):
    if session.get(UserDB, body.username):
        raise HTTPException(status_code=400, detail="That username is already taken.")
    admin = UserDB(username=body.username, name=body.name, role="admin",
                   password_hash=hash_password(body.password))
    session.add(admin); session.commit()
    return {"created": True, "username": admin.username, "name": admin.name}
