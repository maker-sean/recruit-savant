# Recruit Savant MVP

A proof-of-concept web application for transforming amateur baseball data into standardized percentile rankings.

## Features
- **File Upload**: Supports CSV and XLSX formats.
- **Dynamic Column Mapping**: Map your raw data columns to the 10 Standard Target Metrics.
- **Robust Calculation**: Calculates 1-100 percentile ranks for the entire peer group.
- **Directionality Handling**: Correctly inverts rankings for "Lower is Better" metrics (K%, Chase%, Whiff%).
- **Visual Output**: Color-coded table matching Baseball Savant's aesthetic.

## Setup & Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    python app.py
    ```

3.  **Access**:
    Open your browser and navigate to `http://127.0.0.1:5000`.

## Percentile Calculation Logic

The application uses `pandas.DataFrame.rank(pct=True)` to calculate percentiles.

- **Formula**: `Percentile = Rank / Total_Count * 100` (rounded to nearest integer).
- **Missing Data**: Players with missing values (`NaN`) for a specific metric are excluded from the ranking for that metric only. They will appear as `N/A` in the output.
- **Directionality**:
    - **Higher is Better** (Max EV, Avg EV, HardHit%, Barrel%, xwOBA, xSLG, BB%):
        - Ranked in **Ascending** order.
        - Highest value gets the highest percentile (100).
    - **Lower is Better** (K%, Chase%, Whiff%):
        - Ranked in **Descending** order.
        - Lowest value gets the highest percentile (100).

## Project Structure
- `app.py`: Main Flask application entry point.
- `processing.py`: Core logic for data loading, cleaning, and calculation.
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS styles.
