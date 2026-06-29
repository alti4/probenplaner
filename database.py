import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Lokal: ./probenplaner.db  |  Docker: /app/data/probenplaner.db (via DB_PATH)
_db_pfad = os.getenv("DB_PATH", "./probenplaner.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_pfad}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
