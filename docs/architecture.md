# System Architecture

The Hierarchical Long-Horizon Manipulation Planner (HLMP) is a modular, research-oriented robotics framework. It decouples high-level task planning from low-level physical skill execution, connected by a robust task state and recovery manager.

## High-Level Data Flow

1. **User Interface**: The Android client (or raw API calls) submits a natural language goal.
2. **REST API**: FastAPI (`src/hlmp/api/routes.py`) accepts the request and maintains active tasks in memory and a SQLite database.
3. **Planning Layer**:
   - `HierarchicalPlanner` / `HybridPlanner` decompose the goal into an ordered list of `Subgoal`s.
   - Subgoals map directly to strictly validated skills.
4. **Execution Layer**:
   - `TaskStateManager` queues the subgoals and executes them sequentially in a background thread.
   - Each subgoal instantiates a `Skill` (e.g., `Pick`, `Place`, `Move`) acting upon the `SimulationEnvironment`.
5. **Detection & Recovery**:
   - After a skill executes, the `FailureDetector` checks physics telemetry (collisions, grasp strength).
   - If a failure is detected, the `FailureClassifier` maps it to a `FailureType`.
   - `RecoveryManager` decides whether to retry, re-grasp, or abort based on the `FailureEvent` and task history.

## Key Modules

### `src/hlmp/core/`
Contains `planner.py` for task decomposition and `task_state.py` for managing the execution finite state machine.

### `src/hlmp/sim/`
Encapsulates all interactions with the PyBullet physics engine. `env.py` manages the world, `robot.py` manages the Franka Panda arm kinematics, and `objects.py` manages target and obstacle entities.

### `src/hlmp/recovery/`
Handles robustness. `failure_detector.py` uses heuristic checks. `recovery_manager.py` uses an escalation strategy (Retry -> Regrasp -> Reset -> Abort) to resolve issues dynamically without failing the entire long-horizon plan.

### `src/hlmp/evaluation/`
The benchmarking suite for generating metrics (error propagation, success rates) across different system configurations (e.g. Open Loop vs Adaptive Recovery).

### `src/hlmp/api/`
FastAPI wrappers allowing remote invocation, state polling, and experiment tracking.

### `android/HierarchicalManipulationApp/`
A decoupled, native Kotlin client built with Jetpack Compose that visualizes real-time execution states, failure timelines, and aggregated experimental metrics without duplicating Python business logic.
