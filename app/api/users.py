from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db import crud, models
from app.schemas.user import User, UserUpdate

router = APIRouter()


@router.get("/me", response_model=User)
def read_current_user(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.put("/me", response_model=User)
def update_current_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Update the profile of the currently authenticated user."""
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/", response_model=List[User])
def list_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    _: models.User = Depends(deps.get_current_active_user),
):
    """List all users (requires authentication)."""
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
):
    """Fetch a single user by ID."""
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
