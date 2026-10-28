# Hierarchical Long-Horizon Manipulation Planner (HLMP)

## Abstract
Long-horizon robotic manipulation tasks suffer from cascading error propagation due to uncertainty in perception and physical execution. This project implements a hierarchical task planner coupled with a structured failure detection and adaptive recovery engine. By strictly validating LLM-generated subgoals and classifying mechanical failures in real-time, the system demonstrates significantly improved complete-task success rates over extended horizons.

## Problem Statement & Research Motivation
When a robot executes a 20-step plan, a failure at step 4 often dooms the entire sequence. Current "open-loop" systems cannot adapt, while naive "retry" systems get stuck in local minima. We need a framework that can not only detect *that* a failure occurred, but classify *why* it occurred, and dynamically synthesize a localized recovery strategy without forcing a full task restart.

**Research Question:** *Does structured hierarchical planning combined with explicit failure detection and adaptive recovery improve complete-task success and reduce error propagation as task horizon increases?*

## Key Contributions
1. **Hierarchical Deterministic/LLM Hybrid Planner**: Decomposes abstract natural language goals into validated finite-state subgoals.
2. **Deterministic Failure Classification**: Maps PyBullet physics anomalies into structured enums (`GRASP_FAILURE`, `COLLISION`, `TIMEOUT`).
3. **Adaptive Recovery Manager**: Escalates strategies from simple retries to dynamic re-grasping and repositioning.
4. **Research Evaluation Framework**: Automated benchmarking engine to track success, error propagation, and recovery efficiency across configurable horizons and failure rates.
5. **Decoupled Architecture**: Python backend serving a FastAPI application consumed by a native Android Jetpack Compose Dashboard.

## System Architecture
```text
                     USER
                      │
                      ▼
          ┌─────────────────────┐
          │    Android App      │
          │    Kotlin/Compose   │
          └──────────┬──────────┘
                     │ REST
                     ▼
          ┌─────────────────────┐
          │     FastAPI         │
          │      Backend        │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Hierarchical Planner│
          │  + Task State Mgr   │
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │      PyBullet       │
          │   Robot Simulation  │
          └──────────┬──────────┘
                     │
                FAILURE?
                /      \
              NO        YES
              │          │
              ▼          ▼
          Continue   Recovery Manager
```

## Technology Stack
- **Core/Simulation**: Python 3.10+, PyBullet, NumPy
- **API**: FastAPI, Uvicorn, Pydantic, SQLite
- **Evaluation**: Pandas, Matplotlib, Seaborn, Pytest
- **Client**: Android, Kotlin, Jetpack Compose, Retrofit

## Installation & Configuration
1. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # (or venv\Scripts\activate on Windows)
   ```
2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration**: 
   Modify `config/settings.yaml` to adjust PyBullet GUI flags, LLM enablement, and API ports.

## Running the System

### 1. Start the API Server
```bash
python -m uvicorn src.hlmp.api.server:app --reload
```
API Documentation will be available at `http://localhost:8000/docs`.

### 2. End-to-End Demo (Terminal)
Run a complete, headless walkthrough injecting a controlled failure and recovering from it:
```bash
python scripts/end_to_end_demo.py
```

### 3. Android Dashboard
Open the `android/HierarchicalManipulationApp` folder in Android Studio and deploy to an emulator. Ensure you change the API Base URL in the App's **Settings** screen to your machine's IP if testing on a physical device.

## Research Evaluation & Experiments
To reproduce the empirical findings and generate the final plots:
```bash
python scripts/quick_benchmark.py
```
*Outputs are saved to `results/processed/` and `results/plots/`.*

### Metrics Tracked
- **Complete-Task Success Rate**: Percentage of tasks reaching `COMPLETED` state.
- **Subgoal Completion Rate**: Percentage of individual skills executing successfully.
- **Error Propagation**: Measurement of downstream skills executed in an invalid state.
- **Recovery Success Rate**: Effectiveness of the Adaptive Recovery Manager.

## Project Structure
- `config/`: System YAML configurations.
- `src/hlmp/core/`: Planning algorithms and Task State Manager.
- `src/hlmp/sim/`: PyBullet environments and robot kinematics.
- `src/hlmp/skills/`: Executable primitive actions.
- `src/hlmp/recovery/`: Failure detection, classification, and resolution logic.
- `src/hlmp/evaluation/`: Benchmarking, metrics, and chart generation.
- `src/hlmp/api/`: FastAPI REST integration.
- `scripts/`: Demonstration and evaluation entry points.
- `android/`: Native Jetpack Compose research dashboard.
- `docs/`: In-depth architectural documentation.

## Reproducibility & Limitations
- **Limitations**: The failure detector currently relies heavily on simulated physics telemetry (e.g. exact contact points) which may require adaptation for noisy real-world force-torque sensors.
- **Future Work**: Implementing reinforcement learning for the recovery strategy selection rather than relying on deterministic escalation.

## Citation
*(Placeholder for academic citation once published)*
