import pytest
from fastapi.testclient import TestClient
from src.hlmp.api.server import app
from src.hlmp.database.database import init_db
from src.hlmp.api.dependencies import get_db
import src.hlmp.database.database as db_module

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db("sqlite:///:memory:")

def override_get_db():
    db = db_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hierarchical-manipulation-planner"

def test_create_task(client):
    response = client.post("/api/v1/tasks", json={"goal": "Move the red cube to the target area."})
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["goal"] == "Move the red cube to the target area."
    assert data["status"] == "created"

def test_plan_and_state(client):
    create_resp = client.post("/api/v1/tasks", json={"goal": "Move the red cube to the target area."})
    task_id = create_resp.json()["task_id"]
    
    plan_resp = client.post(f"/api/v1/tasks/{task_id}/plan", json={"planner": "deterministic"})
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["task_id"] == task_id
    assert len(plan_data["subgoals"]) > 0
    
    state_resp = client.get(f"/api/v1/tasks/{task_id}")
    assert state_resp.status_code == 200
    state_data = state_resp.json()
    assert state_data["status"] == "NOT_STARTED"
    assert len(state_data["pending_subgoals"]) == len(plan_data["subgoals"])

def test_invalid_task(client):
    response = client.get("/api/v1/tasks/invalid-id")
    assert response.status_code == 404
