from src.hlmp.evaluation.metrics import calculate_metrics

def test_calculate_metrics():
    results = [
        {
            "total_subgoals": 10,
            "completed_subgoals": 5,
            "task_success": False,
            "successful_recoveries": 1,
            "recovery_attempts": 2
        },
        {
            "total_subgoals": 5,
            "completed_subgoals": 5,
            "task_success": True,
            "successful_recoveries": 0,
            "recovery_attempts": 0
        }
    ]
    df = calculate_metrics(results)
    if df is not None:
        assert df.iloc[0]['error_propagation'] == 0.5
        assert df.iloc[1]['error_propagation'] == 0.0
        assert df.iloc[0]['recovery_success_rate'] == 0.5
        assert df.iloc[1]['recovery_success_rate'] == 0.0
