# Experimental Methodology

## Research Objective
Evaluate whether hierarchical planning coupled with structured adaptive recovery reduces error propagation in long-horizon robotic manipulation tasks compared to baseline open-loop systems.

## Baselines
1. **OPEN_LOOP**: Fixed sequence. 1 failure = Task abort.
2. **HIERARCHICAL_NO_RECOVERY**: Validated sequential planning. 1 failure = Task abort.
3. **HIERARCHICAL_SIMPLE_RETRY**: Validated sequential planning. Failures blindly retry 3 times.
4. **FULL_ADAPTIVE_RECOVERY**: Full hierarchical decomposition + escalating strategy recovery (Regrasp, Reposition).

## Error Propagation Metric
When a single failure cascades and terminates a long-horizon task prematurely, the lost potential logic is calculated as:
`Error Propagation = (Total Subgoals - Completed Subgoals) / Total Subgoals` (If task fails).

## Ablation Methodology
By running varying simulated failure injection rates (0% to 30%), we isolate the statistical significance of explicit failure classification vs simple blind retry loops.
