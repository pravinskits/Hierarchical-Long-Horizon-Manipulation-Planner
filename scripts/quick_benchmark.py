import os
import sys
import logging
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.evaluation.benchmark import BenchmarkRunner
from src.hlmp.evaluation.metrics import calculate_metrics
from src.hlmp.evaluation.compare import ComparisonEngine
from src.hlmp.visualization.plots import PlotGenerator
try:
    import pandas as pd
except ImportError:
    pd = None

def main():
    logging.basicConfig(level=logging.WARNING)
    print("========================================")
    print("QUICK BENCHMARK STARTING")
    print("========================================")
    
    systems = [
        "OPEN_LOOP",
        "HIERARCHICAL_NO_RECOVERY",
        "HIERARCHICAL_SIMPLE_RETRY",
        "FULL_ADAPTIVE_RECOVERY"
    ]
    horizons = [5, 10, 20]
    failure_rates = [0.0, 0.10, 0.20]
    seeds = [1, 2, 3]
    
    runner = BenchmarkRunner(logging.getLogger("Benchmark"))
    results = []
    
    total = len(systems) * len(horizons) * len(failure_rates) * len(seeds)
    count = 0
    
    for sys_name in systems:
        for hor in horizons:
            for fr in failure_rates:
                for seed in seeds:
                    count += 1
                    print(f"Running [{count}/{total}] | Sys: {sys_name} | Hor: {hor} | Fail: {fr} | Seed: {seed}")
                    res = runner.run_single_experiment(sys_name, hor, fr, seed)
                    results.append(res.to_dict())
                    
    # Save Raw
    raw_dir = "results/raw"
    os.makedirs(raw_dir, exist_ok=True)
    
    raw_file = os.path.join(raw_dir, "quick_benchmark_results.json")
    with open(raw_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw results to {raw_file}")
    
    if pd is not None:
        df = calculate_metrics(results)
        df.to_csv(os.path.join(raw_dir, "quick_benchmark_results.csv"), index=False)
        
        # Compare
        comp_dir = "results/processed"
        comp = ComparisonEngine(comp_dir)
        comp.generate_summary_tables(df)
        
        # Plot
        plot_dir = "results/plots"
        pg = PlotGenerator(plot_dir)
        pg.generate_all(df)
    else:
        print("Pandas not installed. Skipping CSV generation, aggregation, and plotting.")

if __name__ == "__main__":
    main()
