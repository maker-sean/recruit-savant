# Recruit Savant MVP Implementation Plan

## Goal Description
Build a proof-of-concept web application that transforms uploaded baseball player data (CSV/XLSX) into standardized percentile rankings (1-100) based on a peer group. The system will handle data cleaning, dynamic column mapping, and specific ranking directionality (Higher/Lower is better).

## User Review Required
> [!IMPORTANT]
> **Percentile Calculation Method**: Will use `pandas.Series.rank(pct=True)` or `scipy.stats.percentileofscore`?
> The user specified: "Use numpy.percentile or pandas.Series.quantile with interpolation='linear'".
> *Correction*: `quantile` returns the value at a percentile. To get the *percentile of a value*, we typically use `rank(pct=True)`.
> However, the user explicitly asked for "1-100 percentile rank".
> I will implement a custom function using `scipy.stats.percentileofscore` (kind='weak') or a manual calculation to ensure exact 1-100 integer mapping as requested, or strictly follow the "interpolation='linear'" instruction if they meant finding the cutoffs.
> *Clarification*: The user said "Calculate the 1-100 percentile rank... Use numpy.percentile or pandas.Series.quantile". This is slightly contradictory. `quantile` *finds* the value for a given percentile. To assign a rank to a value, `rank(pct=True)` is standard.
> *Decision*: I will use `pandas.Series.rank(pct=True)` multiplied by 100 and cast to integer (1-100), handling the interpolation/ties appropriately, as this is the standard "Savant" way (usually strict rank).
> *Re-reading*: "The calculation must use a standard, well-defined Pandas method. Use numpy.percentile or pandas.Series.quantile with interpolation='linear' to ensure a consistent, reproducible rank."
> This might mean they want me to calculate the quantile *values* (0-100) and then bin the players? Or just rank them?
> "Calculate the 1-100 percentile rank for every player".
> I will use `df.rank(pct=True)` as it's the direct inverse of quantile. I'll note this in the README.

## Proposed Changes

### Project Structure
- `app.py`: Main Flask application.
- `processing.py`: Logic for data cleaning, mapping, and calculation.
- `templates/`: HTML templates.
- `static/`: CSS styles.

### Backend (Python/Flask/Pandas)

#### [NEW] [app.py](file:///c:/Users/nsett/.gemini/antigravity/scratch/app.py)
- Routes:
    - `/`: Upload form.
    - `/map_columns`: Display column mapping form.
    - `/process`: Handle mapping submission, calculate, render results.
- Session management to store the uploaded dataframe (or path to temp file).

#### [NEW] [processing.py](file:///c:/Users/nsett/.gemini/antigravity/scratch/processing.py)
- `load_data(filepath)`: Load CSV/XLSX.
- `clean_data(df)`: Handle encoding, delimiters.
- `calculate_percentiles(df, mapping)`:
    - Rename columns based on mapping.
    - Enforce types (floats).
    - Loop through 10 metrics.
    - Handle missing data (exclude from rank).
    - Handle directionality:
        - Higher is Better: Rank ascending.
        - Lower is Better: Rank descending (invert).
    - Calculation: `rank = (series.rank(method='min') / count) * 100` or similar to get 1-100.
    - *Refinement*: User asked for `numpy.percentile` or `quantile`. If I strictly follow that, I might need to calculate the 100 quantile cutoffs and bin the players.
    - *Better approach*: `df[col].rank(pct=True) * 100`. I will use this and round/ceil to get 1-100.

### Frontend (HTML/CSS/JS)

#### [NEW] [templates/index.html](file:///c:/Users/nsett/.gemini/antigravity/scratch/templates/index.html)
- Simple file input form.

#### [NEW] [templates/mapping.html](file:///c:/Users/nsett/.gemini/antigravity/scratch/templates/mapping.html)
- Form showing 10 standard metrics.
- Dropdowns for each metric populated with columns from the uploaded file.

#### [NEW] [templates/results.html](file:///c:/Users/nsett/.gemini/antigravity/scratch/templates/results.html)
- Table displaying Player Name and 10 metrics.
- Cells contain the Percentile Rank (integer).
- Classes applied for color coding.

#### [NEW] [static/style.css](file:///c:/Users/nsett/.gemini/antigravity/scratch/static/style.css)
- Minimal styling.
- Color classes:
    - `.rank-90-100` (Dark Red)
    - `.rank-60-89` (Light Red)
    - `.rank-40-59` (Neutral)
    - `.rank-11-39` (Light Blue)
    - `.rank-1-10` (Dark Blue)

## Verification Plan
### Automated Tests
- None explicitly requested, but I will create a test script `test_calc.py` to verify the ranking logic on a small dummy dataset (including edge cases like NaNs and ties).

### Manual Verification
- Upload a sample CSV.
- Map columns.
- Check if "Lower is Better" metrics (K%) have low raw values mapped to high percentiles.
- Check color coding in the output table.
