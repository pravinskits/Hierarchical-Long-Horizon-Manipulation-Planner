import yaml
from fastapi import HTTPException
import src.hlmp.database.database as db_module

def get_db():
    db = db_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_config():
    try:
        with open("config/settings.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load configuration.")
