from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.SUPABASE_DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        if db.is_active:
            db.close() 