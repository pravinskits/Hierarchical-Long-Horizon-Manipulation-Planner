import os
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    pd = None
    plt = None
    sns = None

class PlotGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_all(self, df: 'pd.DataFrame'):
        if pd is None or plt is None or df is None or df.empty:
            print("matplotlib/pandas not available. Skipping plot generation.")
            return
            
        sns.set_theme(style="whitegrid")
        
        # Plot 1: Task Success vs Horizon (at fixed failure rate)
        plt.figure(figsize=(10, 6))
        failure_rates = df['failure_rate'].unique()
        if len(failure_rates) > 0:
            target_fr = 0.10 if 0.10 in failure_rates else failure_rates[0]
            sub_df = df[df['failure_rate'] == target_fr]
            if not sub_df.empty:
                sns.lineplot(data=sub_df, x='horizon', y='task_success', hue='system', marker='o')
                plt.title(f'Task Success Rate vs Horizon ({target_fr*100}% Failure Rate)')
                plt.ylabel('Success Rate')
                plt.xlabel('Horizon')
                plt.savefig(os.path.join(self.output_dir, "success_vs_horizon.png"))
            plt.close()
            
            # Plot 2: Error Propagation vs Horizon
            plt.figure(figsize=(10, 6))
            if not sub_df.empty:
                sns.lineplot(data=sub_df, x='horizon', y='error_propagation', hue='system', marker='s')
                plt.title(f'Error Propagation vs Horizon ({target_fr*100}% Failure Rate)')
                plt.ylabel('Error Propagation')
                plt.xlabel('Horizon')
                plt.savefig(os.path.join(self.output_dir, "error_prop_vs_horizon.png"))
            plt.close()
            
            # Plot 3: Recovery Success Rate
            plt.figure(figsize=(10, 6))
            if not sub_df.empty:
                sns.lineplot(data=sub_df, x='horizon', y='recovery_success_rate', hue='system', marker='^')
                plt.title(f'Recovery Success Rate vs Horizon ({target_fr*100}% Failure Rate)')
                plt.ylabel('Recovery Success Rate')
                plt.xlabel('Horizon')
                plt.savefig(os.path.join(self.output_dir, "recovery_success_rate.png"))
            plt.close()
            
            # Plot 4: Average Recovery Attempts
            plt.figure(figsize=(10, 6))
            if not sub_df.empty:
                sns.barplot(data=sub_df, x='horizon', y='recovery_attempts', hue='system')
                plt.title(f'Average Recovery Attempts ({target_fr*100}% Failure Rate)')
                plt.ylabel('Attempts')
                plt.xlabel('Horizon')
                plt.savefig(os.path.join(self.output_dir, "average_recovery_attempts.png"))
            plt.close()

            # Plot 5: Execution Time vs Horizon
            plt.figure(figsize=(10, 6))
            if not sub_df.empty:
                sns.lineplot(data=sub_df, x='horizon', y='execution_time', hue='system', marker='o')
                plt.title(f'Execution Time vs Horizon ({target_fr*100}% Failure Rate)')
                plt.ylabel('Execution Time (s)')
                plt.xlabel('Horizon')
                plt.savefig(os.path.join(self.output_dir, "execution_time_vs_horizon.png"))
            plt.close()

        # Plot 6: Task Success vs Failure Rate (at fixed horizon)
        horizons = df['horizon'].unique()
        if len(horizons) > 0:
            target_hor = 10 if 10 in horizons else horizons[0]
            plt.figure(figsize=(10, 6))
            sub_df2 = df[df['horizon'] == target_hor]
            if not sub_df2.empty:
                sns.lineplot(data=sub_df2, x='failure_rate', y='task_success', hue='system', marker='o')
                plt.title(f'Task Success vs Failure Rate (Horizon {target_hor})')
                plt.ylabel('Success Rate')
                plt.xlabel('Failure Rate')
                plt.savefig(os.path.join(self.output_dir, "success_vs_failure_rate.png"))
            plt.close()

        # Plot 7: Failure Distribution
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x='system', y='failure_count')
        plt.title('Total Failure Count Distribution across Systems')
        plt.ylabel('Total Failure Count')
        plt.xlabel('System')
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "failure_distribution.png"))
        plt.close()

        print(f"Plots successfully generated in {self.output_dir}")
