# REST API Documentation

The HLMP API is built on FastAPI and serves at `http://localhost:8000/api/v1/`.

## Endpoints

### 1. `GET /health`
Returns the operational status of the API, simulation availability, and LLM configuration.
- **Response**: `HealthResponse`

### 2. `POST /tasks`
Creates a new tracking record for a manipulation goal.
- **Body**: `{"goal": "string"}`
- **Response**: `TaskResponse` containing the generated UUID.

### 3. `POST /tasks/{task_id}/plan`
Generates the hierarchical plan for the task.
- **Body**: `{"planner": "deterministic" | "groq"}`
- **Response**: `PlanResponse` containing an ordered list of `SubgoalSchema`.

### 4. `GET /tasks/{task_id}`
Polls the active progress of a task.
- **Response**: `TaskStateResponse` detailing completed, pending, and failed subgoals, along with an overall completion percentage.

### 5. `POST /tasks/{task_id}/execute`
Forks a background thread to begin physical execution of the planned subgoals in the PyBullet simulator.
- **Response**: `ExecuteResponse` indicating the background process has started.

### 6. `POST /tasks/{task_id}/abort`
Force-stops a running task and marks it as FAILED.
- **Body**: `{"reason": "string"}`
- **Response**: `AbortResponse`

### 7. `GET /tasks/{task_id}/failures`
Retrieves all classified failure events that occurred during execution.
- **Response**: `List[FailureEventResponse]`

### 8. `GET /tasks/{task_id}/recovery`
Retrieves the history of recovery strategies attempted and their outcomes.
- **Response**: `List[RecoveryEventResponse]`

### 9. `GET /experiments`
Fetches all completed benchmark evaluation iterations for comparative analysis.
- **Response**: `ExperimentsResponse`

### 10. `GET /tasks/{task_id}/results`
Fetches a high-level summary of a completed task's metrics (success rate, failure count).
- **Response**: `ResultsResponse`

## Security Notes
- Endpoints do not accept arbitrary code execution requests. 
- LLM keys (`GROQ_API_KEY`) are managed strictly on the server and are never transmitted to or requested from the client.
