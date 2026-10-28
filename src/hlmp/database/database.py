import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.hlmp.database.models import Base

engine = None
SessionLocal = None

def init_db(database_url: str):
    global engine, SessionLocal
    if database_url.startswith("sqlite:///"):
        path = database_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
