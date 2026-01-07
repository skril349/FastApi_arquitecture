import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

# arrel del paquet "app"
APP_DIR = Path(__file__).resolve().parent  # .../FastApi_arquitecture/app
DEFAULT_DB_PATH = APP_DIR / "blog.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, future=True, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
