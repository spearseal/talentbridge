from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(String, nullable=False)  # "seeker" or "provider"
    is_partner = Column(Boolean, default=False)  # Partner status
    bio = Column(Text)
    location = Column(String)
    skills = Column(Text)  # Comma-separated for POC (use Array in prod)
    experience_years = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    connections_initiated = relationship("Connection", foreign_keys="Connection.user_id")
    connections_received = relationship("Connection", foreign_keys="Connection.connected_user_id")

class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    connected_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    connected_user = relationship("User", foreign_keys=[connected_user_id])

