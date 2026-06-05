# routers/materials.py — course materials.
#   • Students READ materials for their own course.
#   • Trainers & admins ADD / DELETE materials.
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import MaterialDB, MaterialIn, StudentDB
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/materials", tags=["Materials"])


@router.get("", response_model=list[MaterialDB])
def list_materials(session: Session = Depends(get_session), user=Depends(get_current_user)):
    rows = session.exec(select(MaterialDB)).all()
    # A student only sees materials for the course they're enrolled in.
    if user.role == "student" and user.ref_id:
        me = session.get(StudentDB, user.ref_id)
        if me:
            rows = [m for m in rows if m.course == me.course]
    return rows


@router.post("", response_model=MaterialDB, status_code=201)
def add_material(body: MaterialIn, session: Session = Depends(get_session),
                 user=Depends(require_role("admin", "trainer"))):
    material = MaterialDB(**body.model_dump(), uploaded_by=user.name)
    session.add(material); session.commit(); session.refresh(material)
    return material


@router.delete("/{material_id}")
def delete_material(material_id: int, session: Session = Depends(get_session),
                    user=Depends(require_role("admin", "trainer"))):
    material = session.get(MaterialDB, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    session.delete(material); session.commit()
    return {"deleted": material_id}
