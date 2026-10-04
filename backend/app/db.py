import socket
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

db_url = settings.DATABASE_URL

if "@db:" in db_url or "@db/" in db_url:
    try:
        socket.gethostbyname("db")
    except socket.gaierror:
        db_url = db_url.replace("@db:", "@localhost:").replace("@db/", "@localhost/")

if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

try:
    _eng = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
    with _eng.connect() as _conn:
        pass
    engine = _eng
except Exception:
    db_url = "sqlite:///./wini_test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in str(type(dbapi_connection)):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
