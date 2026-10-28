try:
    import pandas as pd
except ImportError:
    pd = None

from typing import List, Dict

def calculate_metrics(results: List[Dict]) -> 'pd.DataFrame':
    if pd is None:
        return None
        
    df = pd.DataFrame(results)
    if df.empty:
        return df

    df['error_propagation'] = df.apply(
        lambda row: (row['total_subgoals'] - row['completed_subgoals']) / row['total_subgoals'] if row['total_subgoals'] > 0 and not row['task_success'] else 0.0,
        axis=1
    )
    
    df['recovery_success_rate'] = df.apply(
        lambda row: row['successful_recoveries'] / row['recovery_attempts'] if row['recovery_attempts'] > 0 else 0.0,
        axis=1
    )
    
    return df

def aggregate_metrics(df: 'pd.DataFrame') -> 'pd.DataFrame':
    if df is None or df.empty:
        return df
    grouped = df.groupby(['system', 'horizon', 'failure_rate']).agg({
        'task_success': 'mean',
        'completed_subgoals': 'mean',
        'error_propagation': 'mean',
        'recovery_success_rate': 'mean',
        'recovery_attempts': 'mean',
        'execution_time': 'mean'
    }).reset_index()
    return grouped
