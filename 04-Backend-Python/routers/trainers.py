# routers/trainers.py — /api/trainers endpoints (CRUD). Admin-managed.
from fastapi import APIRouter, Depends, HTTPException
import data
from models import Trainer, TrainerIn
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/trainers", tags=["Trainers"])


@router.get("", response_model=list[Trainer])
def list_trainers(user=Depends(get_current_user)):
    return data.trainers


@router.post("", response_model=Trainer, status_code=201)
def add_trainer(body: TrainerIn, user=Depends(require_role("admin"))):
    new = {"id": data.next_id(data.trainers, "TRN"), **body.model_dump()}
    data.trainers.append(new)
    return new


@router.put("/{trainer_id}", response_model=Trainer)
def update_trainer(trainer_id: str, body: TrainerIn, user=Depends(require_role("admin"))):
    for t in data.trainers:
        if t["id"] == trainer_id:
            t.update(body.model_dump())
            return t
    raise HTTPException(status_code=404, detail="Trainer not found")


@router.delete("/{trainer_id}")
def delete_trainer(trainer_id: str, user=Depends(require_role("admin"))):
    before = len(data.trainers)
    data.trainers[:] = [t for t in data.trainers if t["id"] != trainer_id]
    if len(data.trainers) == before:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return {"deleted": trainer_id}
