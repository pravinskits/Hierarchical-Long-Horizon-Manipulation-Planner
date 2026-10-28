from src.hlmp.evaluation.compare import ComparisonEngine
from src.hlmp.evaluation.metrics import calculate_metrics
import os

def test_generate_summary_tables(tmp_path):
    results = [
        {"system": "A", "horizon": 5, "failure_rate": 0.1, "task_success": True, "total_subgoals": 5, "completed_subgoals": 5, "recovery_attempts": 0, "successful_recoveries": 0, "execution_time": 1.0},
        {"system": "A", "horizon": 5, "failure_rate": 0.1, "task_success": False, "total_subgoals": 5, "completed_subgoals": 2, "recovery_attempts": 1, "successful_recoveries": 0, "execution_time": 1.0}
    ]
    df = calculate_metrics(results)
    if df is not None:
        comp = ComparisonEngine(str(tmp_path))
        comp.generate_summary_tables(df)
        assert os.path.exists(os.path.join(str(tmp_path), "final_comparison.csv"))
