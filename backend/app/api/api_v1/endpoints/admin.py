from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db import session, crud, models
from app.schemas import user as user_schema
from app.api import deps

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/users", response_model=List[user_schema.User])
def read_users(
    db: Session = Depends(session.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    return crud.get_users(db)

@router.post("/users", response_model=user_schema.User)
def create_user(
    user_in: user_schema.UserCreate,
    db: Session = Depends(session.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    user = crud.get_user_by_code(db, code=user_in.code)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_user(db, **user_in.dict())

@router.put("/users/{user_code}", response_model=user_schema.User)
def update_user(
    user_code: str,
    user_in: user_schema.UserUpdate,
    db: Session = Depends(session.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    user = crud.get_user_by_code(db, user_code)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    for field, value in user_in.dict(exclude_unset=True).items():
        crud.update_user_field(db, user_code, field, value)
    
    return user

@router.delete("/users/{user_code}")
def delete_user(
    user_code: str,
    db: Session = Depends(session.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    if crud.delete_user(db, user_code):
        return {"msg": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/users/{user_code}/reset-secret")
def reset_user_secret(
    user_code: str,
    payload: user_schema.ResetSecretRequest,
    db: Session = Depends(session.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    if len(payload.new_secret.strip()) < 6:
        raise HTTPException(status_code=400, detail="Secret must be at least 6 characters")
    user = crud.reset_user_secret(db, user_code, payload.new_secret.strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("admin_reset_user_secret admin=%s target=%s", current_admin.code, user_code)
    return {"msg": "User secret reset successfully"}
