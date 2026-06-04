from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import Base
from app.db import models
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate

# ── Generic CRUD base ──────────────────────────────────────────────────────────
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


# ── User CRUD ──────────────────────────────────────────────────────────────────
class CRUDUser(CRUDBase[models.User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> models.User:
        db_obj = models.User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            bio=obj_in.bio,
            location=obj_in.location,
            skills=obj_in.skills,
            experience_years=obj_in.experience_years,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: models.User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
    ) -> models.User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[models.User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


# ── Connection CRUD ────────────────────────────────────────────────────────────
class CRUDConnection(CRUDBase[models.Connection, Any, Any]):
    def get_user_connections(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Connection]:
        return (
            db.query(models.Connection)
            .filter(
                (models.Connection.user_id == user_id)
                | (models.Connection.connected_user_id == user_id)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_existing(
        self, db: Session, *, user_id: int, connected_user_id: int
    ) -> Optional[models.Connection]:
        return (
            db.query(models.Connection)
            .filter(
                (
                    (models.Connection.user_id == user_id)
                    & (models.Connection.connected_user_id == connected_user_id)
                )
                | (
                    (models.Connection.user_id == connected_user_id)
                    & (models.Connection.connected_user_id == user_id)
                )
            )
            .first()
        )


user = CRUDUser(models.User)
connection = CRUDConnection(models.Connection)
