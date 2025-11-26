# Automated Test Results

**Date**: 2025-11-19
**Test Script**: `test_calc.py`

## Output
```
Input Data:
  Name  ExitVelocity  Strikeouts  SwingLength
0    A         100.0          10          6.0
1    B          90.0          20          6.5
2    C          80.0          30          7.0
3    D          70.0          40          7.5
4    E           NaN          50          8.0

Calculated Percentiles:
  Player Name  Max EV     K%  Swing Length
0           A   100.0  100.0         100.0
1           B    75.0   80.0          80.0
2           C    50.0   60.0          60.0
3           D    25.0   40.0          40.0
4           E     NaN   20.0          20.0

All tests passed!
```

## Verification
- **Max EV (Higher is Better)**: Player A (100.0) -> Rank 100. Correct.
- **K% (Lower is Better)**: Player A (10) -> Rank 100. Correct.
- **Swing Length (Lower is Better)**: Player A (6.0) -> Rank 100. Correct.
