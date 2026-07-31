from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {"connect_timeout": 10}
engine_options = {"connect_args": connect_args}
if not settings.DATABASE_URL.startswith("sqlite"):
    # Supabase Pooler can close idle TLS connections. Validate a connection
    # before each checkout and replace it before it becomes stale.
    engine_options.update(pool_pre_ping=True, pool_recycle=1800, pool_timeout=30)

engine = create_engine(settings.DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_database_status = {"available": False, "detail": "Database has not been checked."}

class Base(DeclarativeBase):
    pass

def check_database_connection() -> bool:
    """Check database reachability without mutating its schema."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        _database_status.update(available=True, detail="Database connection is available.")
        return True
    except SQLAlchemyError:
        _database_status.update(available=False, detail="Database connection is unavailable.")
        return False


def get_database_status() -> dict[str, str | bool]:
    return _database_status.copy()
