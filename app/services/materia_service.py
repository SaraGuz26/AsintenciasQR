from sqlalchemy.orm import Session
from app.models.materia import Materia
from app.schemas.materia import MateriaCreate, MateriaUpdate

class MateriaService:

    def list(self, db: Session):
        return db.query(Materia).all()

    def create(self, db: Session, data: MateriaCreate):
        obj = Materia(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, materia_id: int, data: MateriaUpdate):
        obj = db.query(Materia).filter(Materia.id == materia_id).first()
        if not obj:
            return None
        
        for k, v in data.dict(exclude_unset=True).items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)
        return obj

    def remove(self, db: Session, materia_id: int):
        obj = db.query(Materia).filter(Materia.id == materia_id).first()
        if obj:
            db.delete(obj)
            db.commit()

materia_service = MateriaService()
