# routers/trainers.py — Trainer CRUD backed by the database.
# Admin-only writes. Adding a trainer auto-creates their LOGIN account so they
# can sign in and run their classes; deleting removes that account too.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session, next_id
from models import TrainerDB, TrainerIn, UserDB
from auth import get_current_user, require_role, create_user_account

router = APIRouter(prefix="/api/trainers", tags=["Trainers"])


@router.get("", response_model=list[TrainerDB])
def list_trainers(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return session.exec(select(TrainerDB)).all()


@router.post("", status_code=201)
def add_trainer(body: TrainerIn, session: Session = Depends(get_session),
                user=Depends(require_role("admin"))):
    trainer = TrainerDB(id=next_id(session, TrainerDB, "TRN"), **body.model_dump())
    session.add(trainer)
    account = create_user_account(session, name=trainer.name, role="trainer",
                                  password="trainer123", ref_id=trainer.id)
    session.commit(); session.refresh(trainer)
    return {"trainer": trainer, "login": {"username": account.username, "password": "trainer123"}}


@router.put("/{trainer_id}", response_model=TrainerDB)
def update_trainer(trainer_id: str, body: TrainerIn, session: Session = Depends(get_session),
                   user=Depends(require_role("admin"))):
    trainer = session.get(TrainerDB, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    for key, value in body.model_dump().items():
        setattr(trainer, key, value)
    session.add(trainer); session.commit(); session.refresh(trainer)
    return trainer


@router.delete("/{trainer_id}")
def delete_trainer(trainer_id: str, session: Session = Depends(get_session),
                   user=Depends(require_role("admin"))):
    trainer = session.get(TrainerDB, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    account = session.exec(select(UserDB).where(UserDB.ref_id == trainer_id)).first()
    if account:
        session.delete(account)
    session.delete(trainer); session.commit()
    return {"deleted": trainer_id}
