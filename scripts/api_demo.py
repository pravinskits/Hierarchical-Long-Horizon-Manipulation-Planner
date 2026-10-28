import time
import requests

API_URL = "http://127.0.0.1:8000/api/v1"

def run_demo():
    print("=== HLMP API Demo ===")
    
    # 1. Health Check
    print("\n1. Checking Health...")
    resp = requests.get(f"{API_URL}/health")
    print(resp.json())
    
    # 2. Create Task
    print("\n2. Creating Task...")
    goal = "Move the red cube to the target area."
    resp = requests.post(f"{API_URL}/tasks", json={"goal": goal})
    task = resp.json()
    task_id = task["task_id"]
    print(f"Task created: {task_id}")
    
    # 3. Generate Plan
    print("\n3. Generating Plan (Deterministic)...")
    resp = requests.post(f"{API_URL}/tasks/{task_id}/plan", json={"planner": "deterministic"})
    plan = resp.json()
    print(f"Generated {len(plan['subgoals'])} subgoals")
    for sg in plan['subgoals']:
        print(f"  - {sg['skill_name']}: {sg['parameters']}")
        
    # 4. Check State
    print("\n4. Checking Initial State...")
    resp = requests.get(f"{API_URL}/tasks/{task_id}")
    state = resp.json()
    print(f"Status: {state['status']} | Progress: {state['progress_percentage']}%")
    
    # 5. Start Execution
    print("\n5. Starting Execution...")
    resp = requests.post(f"{API_URL}/tasks/{task_id}/execute")
    print(resp.json())
    
    # 6. Poll Status
    print("\n6. Polling Status...")
    for _ in range(10):
        time.sleep(1)
        resp = requests.get(f"{API_URL}/tasks/{task_id}")
        state = resp.json()
        print(f"Status: {state['status']} | Progress: {state['progress_percentage']}%")
        if state['status'] in ("COMPLETED", "FAILED"):
            break
            
    # 7. Check Failures and Recoveries
    print("\n7. Checking Events...")
    fails = requests.get(f"{API_URL}/tasks/{task_id}/failures").json()
    recs = requests.get(f"{API_URL}/tasks/{task_id}/recovery").json()
    print(f"Failures recorded: {len(fails)}")
    print(f"Recoveries attempted: {len(recs)}")
    
    # 8. Check Final Results
    print("\n8. Final Results...")
    res = requests.get(f"{API_URL}/tasks/{task_id}/results").json()
    print(res)
    
if __name__ == "__main__":
    run_demo()
