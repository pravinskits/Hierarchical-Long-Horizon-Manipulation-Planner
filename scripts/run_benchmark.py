import argparse
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.hlmp.evaluation.benchmark import BenchmarkRunner

def main():
    parser = argparse.ArgumentParser(description="Run HLMP Benchmark")
    parser.add_argument("--system", type=str, required=True, help="System to test")
    parser.add_argument("--horizon", type=int, required=True, help="Horizon length")
    parser.add_argument("--failure-rate", type=float, required=True, help="Failure rate")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    runner = BenchmarkRunner(logging.getLogger("BenchmarkRunner"))
    
    print(f"Running {args.system} | Horizon {args.horizon} | Failure Rate {args.failure_rate} | Seed {args.seed}")
    res = runner.run_single_experiment(args.system, args.horizon, args.failure_rate, args.seed)
    
    print(f"\nTask Success: {res.task_success}")
    print(f"Completed Subgoals: {res.completed_subgoals}/{res.total_subgoals}")
    print(f"Failure Count: {res.failure_count}")
    print(f"Recovery Attempts: {res.recovery_attempts}")
    print(f"Successful Recoveries: {res.successful_recoveries}")
    print(f"Execution Time: {res.execution_time:.2f}s")
    print(f"Task Status: {res.task_status}")
    
if __name__ == "__main__":
    main()
