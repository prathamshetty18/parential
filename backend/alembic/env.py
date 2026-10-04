import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db import Base
import app.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import socket
from sqlalchemy import create_engine

database_url = settings.DATABASE_URL
if "@db:" in database_url or "@db/" in database_url:
    try:
        socket.gethostbyname("db")
    except socket.gaierror:
        database_url = database_url.replace("@db:", "@localhost:").replace("@db/", "@localhost/")

if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

try:
    _eng = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
    with _eng.connect() as _conn:
        pass
except Exception:
    database_url = "sqlite:///./test_auth_children.db"

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
