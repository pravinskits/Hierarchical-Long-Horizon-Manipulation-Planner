from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TaskRecord(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    goal = Column(String, nullable=False)
    status = Column(String, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)
    planner_type = Column(String, nullable=True)
    plan_json = Column(Text, nullable=True)

class FailureRecord(Base):
    __tablename__ = "failure_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, index=True)
    timestamp = Column(Float)
    skill_name = Column(String)
    subgoal_id = Column(String)
    failure_type = Column(String)
    message = Column(String)

class RecoveryRecord(Base):
    __tablename__ = "recovery_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, index=True)
    timestamp = Column(Float)
    strategy = Column(String)
    failure_type = Column(String)
    success = Column(Boolean)
