from src.hlmp.evaluation.benchmark import BenchmarkRunner

def test_open_loop_failure():
    runner = BenchmarkRunner()
    res = runner.run_single_experiment("OPEN_LOOP", horizon=3, failure_rate=1.0, seed=1)
    assert not res.task_success
    assert res.task_status == "FAILED"
    assert res.failure_count > 0

def test_full_recovery_success():
    runner = BenchmarkRunner()
    res = runner.run_single_experiment("FULL_ADAPTIVE_RECOVERY", horizon=3, failure_rate=0.0, seed=1)
    assert res.task_success
    assert res.completed_subgoals == 3
