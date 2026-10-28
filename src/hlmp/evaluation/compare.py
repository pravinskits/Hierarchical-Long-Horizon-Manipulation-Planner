import os
try:
    import pandas as pd
except ImportError:
    pd = None
from typing import List, Dict
from src.hlmp.evaluation.metrics import aggregate_metrics

class ComparisonEngine:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_summary_tables(self, df: 'pd.DataFrame'):
        if pd is None or df is None or df.empty:
            return
        agg = aggregate_metrics(df)
        agg.to_csv(os.path.join(self.output_dir, "final_comparison.csv"), index=False)
        print(f"Comparison summary generated at {self.output_dir}/final_comparison.csv")
