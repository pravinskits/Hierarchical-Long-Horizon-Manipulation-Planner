# Evaluation Results

This folder contains the deterministic experiment outputs for HLMP.

- `raw/`: Unfiltered JSON logs and base CSV data recorded directly from `BenchmarkRunner`.
- `processed/`: Aggregated Pandas summaries calculating Mean/StdDev metrics across Random Seeds.
- `plots/`: PNG graphs visually analyzing Task Success vs Horizon and Error Propagation decay.

## Reproducibility
To reproduce the experimental plots:
```bash
python scripts/quick_benchmark.py
```
This forces all 4 systems through identical deterministic random seeds ensuring completely fair baseline comparisons.
