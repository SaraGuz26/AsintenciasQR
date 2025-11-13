from contextlib import contextmanager
from app.db.session import SessionLocal
from app.services.docente_service import docente_service

@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:  # noqa
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_docente_service():
    return docente_service