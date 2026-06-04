from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db import crud, models
from app.schemas.connection import Connection, ConnectionCreate

router = APIRouter()

PARTNER_THRESHOLD = 20


def _check_and_upgrade_partner_status(user_id: int, db: Session) -> None:
    """Upgrade a user to Partner status when they reach the threshold of
    same-role connections."""
    user = crud.user.get(db, id=user_id)
    if not user or user.is_partner:
        return

    if user.role == "seeker":
        relevant_count = (
            db.query(models.Connection)
            .filter(
                (
                    (models.Connection.user_id == user_id)
                    & models.Connection.connected_user.has(role="seeker")
                )
                | (
                    (models.Connection.connected_user_id == user_id)
                    & models.Connection.user.has(role="seeker")
                )
            )
            .count()
        )
    else:  # provider
        relevant_count = (
            db.query(models.Connection)
            .filter(
                (
                    (models.Connection.user_id == user_id)
                    & models.Connection.connected_user.has(role="provider")
                )
                | (
                    (models.Connection.connected_user_id == user_id)
                    & models.Connection.user.has(role="provider")
                )
            )
            .count()
        )

    if relevant_count >= PARTNER_THRESHOLD:
        crud.user.update(db, db_obj=user, obj_in={"is_partner": True})
        print(
            f"🎉 PARTNER UPGRADE: {user.full_name} ({user.role}) "
            f"now has {relevant_count} {user.role} connections"
        )


@router.post("/", response_model=Connection, status_code=status.HTTP_201_CREATED)
def create_connection(
    *,
    db: Session = Depends(deps.get_db),
    connection_in: ConnectionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Create a new connection and trigger Partner-status check for both users."""
    if connection_in.connected_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot connect to yourself",
        )

    target = crud.user.get(db, id=connection_in.connected_user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    existing = crud.connection.get_existing(
        db,
        user_id=current_user.id,
        connected_user_id=connection_in.connected_user_id,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection already exists",
        )

    connection = models.Connection(
        user_id=current_user.id,
        connected_user_id=connection_in.connected_user_id,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    # Check Partner status for both sides of the new connection
    _check_and_upgrade_partner_status(current_user.id, db)
    _check_and_upgrade_partner_status(connection_in.connected_user_id, db)

    return connection


@router.get("/", response_model=List[Connection])
def list_connections(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Return all connections for the currently authenticated user."""
    return crud.connection.get_user_connections(
        db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    connection_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Remove an existing connection (only the initiating user may delete it)."""
    connection = crud.connection.get(db, id=connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )
    if connection.user_id != current_user.id and connection.connected_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to remove this connection",
        )
    crud.connection.remove(db, id=connection_id)
