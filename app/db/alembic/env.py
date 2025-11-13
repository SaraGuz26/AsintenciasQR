from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
import os

# importa la Base con TODOS los modelos ya importados en base.py
from app.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://asistencias_user:asistencias_pass@db:3306/asistencias_db?charset=utf8mb4&"
)

def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": DB_URL},
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
