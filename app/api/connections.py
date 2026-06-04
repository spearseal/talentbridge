from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import models, crud
from app.api import deps
from app.schemas import connection as connection_schema

router = APIRouter()

def check_and_upgrade_partner_status(user_id: int, db: Session):
    """Core Partner upgrade logic - runs on every new connection"""
    user = crud.user.get(db, id=user_id)
    if not user or user.is_partner:
        return
    
    # Count relevant connections based on user role
    if user.role == "seeker":
        # Count connections to OTHER SEEKERS only
        seeker_connections = db.query(models.Connection).filter(
            ((models.Connection.user_id == user_id) & (models.Connection.connected_user.has(role="seeker")) |
             ((models.Connection.connected_user_id == user_id) & (models.Connection.user.has(role="seeker")))
        ).count()
        relevant_count = seeker_connections
    else:  # provider
        # Count connections to OTHER PROVIDERS only
        provider_connections = db.query(models.Connection).filter(
            ((models.Connection.user_id == user_id) & (models.Connection.connected_user.has(role="provider")) |
             ((models.Connection.connected_user_id == user_id) & (models.Connection.user.has(role="provider")))
        ).count()
        relevant_count = provider_connections
    
    # Upgrade if threshold met (20+)
    if relevant_count >= 20:
        crud.user.update(db, db_obj=user, obj_in={"is_partner": True})
        print(f"🎉 PARTNER UPGRADE: {user.full_name} ({user.role}) now has {relevant_count} {user.role} connections")

@router.post("/", response_model=connection_schema.Connection)
def create_connection(
    *,
    db: Session = Depends(deps.get_db),
    connection_in: connection_schema.ConnectionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Create a new connection and trigger Partner check"""
    # Prevent self-connection
    if connection_in.connected_user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot connect to yourself"
        )
    
    # Check if connection already exists (either direction)
    existing = db.query(models.Connection).filter(
        ((models.Connection.user_id == current_user.id) & 
         (models.Connection.connected_user_id == connection_in.connected_user_id)) |
        ((models.Connection.user_id == connection_in.connected_user_id) & 
         (models.Connection.connected_user_id == current_user.id))
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Connection already exists"
        )
    
    # Create connection
    connection = models.Connection(
        user_id=current_user.id,
        connected_user_id=connection_in.connected_user_id
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    # --- CRITICAL PART: Check Partner Status for BOTH USERS ---
    check_and_upgrade_partner_status(current_user.id, db)
    check_and_upgrade_partner_status(connection_in.connected_user_id, db)
    
    return connection

@router.get("/", response_model=List[connection_schema.Connection])
def read_connections(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get current user's connections"""
    connections = db.query(models.Connection).filter(
        (models.Connection.user_id == current_user.id) |
        (models.Connection.connected_user_id == current_user.id)
    ).offset(skip).limit(limit).all()
    return connections

