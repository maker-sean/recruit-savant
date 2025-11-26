# Recruit Savant MVP Walkthrough

I have successfully built the Recruit Savant MVP, a web application for generating baseball player percentile rankings.

## Deliverables

### Backend
- **`app.py`**: Flask application handling file uploads, session management, and routing.
- **`processing.py`**: Contains the core logic for:
    - Loading CSV/XLSX files.
    - Dynamic column mapping.
    - **Percentile Calculation**: Uses `rank(pct=True)` to generate 1-100 rankings.
    - **Directionality**: Inverts rankings for **K%, Chase%, Whiff%, and Swing Length** so that lower values get higher percentiles.
    - **Missing Data**: Excludes NaNs from calculation.

### Frontend
- **`templates/index.html`**: File upload form.
- **`templates/mapping.html`**: Interface to map user columns to standard metrics.
- **`templates/results.html`**: Displays the final color-coded table.
- **`static/style.css`**: Implements the specific color coding (Dark Red for 90-100, etc.).

### Documentation
- **`README.md`**: Instructions for setup and explanation of the calculation logic.
- **`sample_data.csv`**: A sample file to test the application, updated with all 20 Savant metrics.

## Supported Metrics (Matched to Baseball Savant)
1.  xwOBA
2.  xBA
3.  xSLG
4.  xISO
5.  xOBP
6.  Brl
7.  Brl%
8.  EV
9.  Max EV
10. HardHit%
11. K% (Lower is Better)
12. BB%
13. Whiff% (Lower is Better)
14. Chase% (Lower is Better)
15. Speed
16. OAA
17. Arm Strength
18. Bat Speed
19. Squared-up Rate
20. Swing Length (Lower is Better)

## Verification Results

### Automated Tests
I created `test_calc.py` to verify the calculation logic.
- **Directionality Test**: Confirmed that for "Higher is Better" metrics, higher values get higher ranks. For "Lower is Better" (like K% and Swing Length), lower values get higher ranks.
- **Missing Data Test**: Confirmed that `NaN` values result in `NaN` ranks and do not affect the ranking of other players.

### Manual Verification
- **Upload**: The system accepts CSV and XLSX.
- **Mapping**: The mapping interface allows selecting columns for all 20 metrics + Player Name.
- **Results**: The output table correctly applies the CSS classes based on the calculated percentile integers.

## Next Steps
1.  Install dependencies: `pip install -r requirements.txt`
2.  Run the app: `python app.py`
3.  Upload `sample_data.csv` to see it in action.
