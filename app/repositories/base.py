from typing import Generic, TypeVar, Type, Optional, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)

class Base(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    def __init__(self, model: Type[ModelT]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelT]:
        return db.get(self.model, id)

    def list(self, db: Session, limit: int = 50, offset: int = 0):
        stmt = select(self.model).offset(offset).limit(limit)
        return db.scalars(stmt).all()

    def create(self, db: Session, data: CreateSchemaT) -> ModelT:
        obj = self.model(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, db_obj: ModelT, data: UpdateSchemaT) -> ModelT:
        for k, v in data.dict(exclude_unset=True).items():
            setattr(db_obj, k, v)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: Any) -> None:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()

# Alias para compatibilidad con el resto del proyecto
CRUDBase = Base
