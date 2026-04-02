import logging
from pathlib import Path

from sqlalchemy import event, create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# Hybrid database engine setup
BACKEND_DIR = Path(__file__).resolve().parents[2]
SQLITE_DB_PATH = BACKEND_DIR / settings.SQLITE_DB_NAME
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL or f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

# Special setup for SQLite to enable foreign keys
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema():
    """
    Best-effort lightweight schema migration for existing DBs.
    We avoid heavyweight migration tooling to keep the app simple.
    """
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "secret_hash" not in cols:
                if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
                    with engine.connect() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN secret_hash VARCHAR"))
                        conn.commit()
                else:
                    with engine.connect() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS secret_hash VARCHAR"))
                        conn.commit()
    except Exception:
        # If migration fails, create_all will still work on fresh DBs.
        # Existing DBs might need manual migration depending on the engine.
        logger.exception("ensure_schema_failed")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
