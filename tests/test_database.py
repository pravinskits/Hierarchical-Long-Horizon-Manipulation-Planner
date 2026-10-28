import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.hlmp.database.models import Base
from src.hlmp.database.repository import TaskRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_create_and_get_task(db_session):
    repo = TaskRepository(db_session)
    task = repo.create_task("task-123", "Move the block")
    assert task.id == "task-123"
    assert task.goal == "Move the block"
    assert task.status == "NOT_STARTED"
    
    fetched = repo.get_task("task-123")
    assert fetched is not None
    assert fetched.id == "task-123"

def test_update_task_status(db_session):
    repo = TaskRepository(db_session)
    repo.create_task("task-123", "Move the block")
    
    repo.update_task_status("task-123", "RUNNING", 50.0)
    task = repo.get_task("task-123")
    assert task.status == "RUNNING"
    assert task.progress_percentage == 50.0

def test_add_and_get_failures(db_session):
    repo = TaskRepository(db_session)
    repo.add_failure("task-123", "pick", "sg-1", "GRASP_FAILURE", "Slipped")
    
    failures = repo.get_failures("task-123")
    assert len(failures) == 1
    assert failures[0].skill_name == "pick"
    assert failures[0].failure_type == "GRASP_FAILURE"

def test_add_and_get_recoveries(db_session):
    repo = TaskRepository(db_session)
    repo.add_recovery("task-123", "RETRY", "GRASP_FAILURE", True)
    
    recs = repo.get_recoveries("task-123")
    assert len(recs) == 1
    assert recs[0].strategy == "RETRY"
    assert recs[0].success is True
