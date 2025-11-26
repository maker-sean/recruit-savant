import pandas as pd
import numpy as np
import io

# Standard Target Metrics
TARGET_METRICS = [
    "xwOBA",
    "xBA",
    "xSLG",
    "xISO",
    "xOBP",
    "Brl",
    "Brl%",
    "EV",
    "Max EV",
    "HardHit%",
    "K%",
    "BB%",
    "Whiff%",
    "Chase%",
    "Speed",
    "OAA",
    "Arm Strength",
    "Bat Speed",
    "Squared-up Rate",
    "Swing Length"
]

# Metrics where Lower is Better (so we invert the rank)
LOWER_IS_BETTER = [
    "K%",
    "Chase%",
    "Whiff%",
    "Swing Length"
]

def load_data(file_storage):
    """
    Loads data from a Flask FileStorage object (CSV or XLSX).
    """
    filename = file_storage.filename
    if filename.endswith('.csv'):
        # Try reading with default utf-8, then latin1 if that fails
        try:
            df = pd.read_csv(file_storage)
        except UnicodeDecodeError:
            file_storage.seek(0)
            df = pd.read_csv(file_storage, encoding='latin1')
    elif filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_storage)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or XLSX.")
    return df

def clean_data(df):
    """
    Basic cleaning: remove empty rows/cols if necessary.
    For now, we just return the df as is, assuming the user wants to map columns first.
    """
    return df

def calculate_percentiles(df, mapping):
    """
    Calculates 1-100 percentile ranks for the mapped metrics.
    
    Args:
        df (pd.DataFrame): The raw dataframe.
        mapping (dict): Dictionary mapping 'Standard Metric' -> 'User Column'.
    
    Returns:
        pd.DataFrame: DataFrame with Player Name and Percentile Ranks.
    """
    # 1. Create a new DF with just the mapped columns
    # We assume 'Player Name' is also mapped or we need to ask for it.
    # For MVP, let's assume the user selects a column for 'Player Name' too, 
    # or we just keep all columns and append ranks?
    # The requirement says: "output a single... table displaying the list of players and their final... Percentile Ranks"
    # So we need a Player Name column. I'll add that to the mapping requirement.
    
    result_df = pd.DataFrame()
    
    # Handle Player Name
    player_col = mapping.get('Player Name')
    if player_col and player_col in df.columns:
        result_df['Player Name'] = df[player_col]
    else:
        # If no player name mapped, use index or a default
        result_df['Player Name'] = df.index.astype(str)

    for metric in TARGET_METRICS:
        user_col = mapping.get(metric)
        if not user_col or user_col not in df.columns:
            # If not mapped, fill with N/A
            result_df[metric] = np.nan
            continue
        
        # 2. Type Enforcement: Coerce to numeric, errors='coerce' turns non-numbers to NaN
        series = pd.to_numeric(df[user_col], errors='coerce')
        
        # 3. Percentile Calculation
        # We need 1-100.
        # pd.rank(pct=True) gives 0.0 to 1.0. 
        # We multiply by 100.
        # We want strict 1-100 integers.
        # Handling NaNs: rank() automatically skips NaNs (assigns NaN).
        
        if metric in LOWER_IS_BETTER:
            # Lower is better: Rank Descending (Ascending=False)
            # Example: K%. Lowest K% gets highest rank (100).
            # So we rank ascending=False.
            # 1% K% -> Rank 1 (Best) -> Wait.
            # "Lowest K% should receive the 99th or 100th percentile rank"
            # So Lowest Value = High Percentile.
            # If we use rank(ascending=False), the Highest Value gets Rank 1 (low percentile). 
            # The Lowest Value gets Rank N (high percentile).
            # Let's verify: [10, 20, 30]. rank(ascending=False) -> 10 is 3rd, 20 is 2nd, 30 is 1st.
            # pct=True: 10 is 1.0 (100%), 30 is 0.33.
            # So yes, ascending=False gives the lowest value the highest percentile.
            ranks = series.rank(pct=True, ascending=False)
        else:
            # Higher is better: Rank Ascending.
            # Highest Value = High Percentile.
            ranks = series.rank(pct=True, ascending=True)
            
        # Convert to 1-100 scale
        # rank(pct=True) can return e.g. 0.5. * 100 = 50.
        # We want integers. Round or Ceil?
        # Usually percentiles are 1-99 or 1-100.
        # Let's use round(decimals=0).
        # Also handle the case where rank is NaN.
        
        result_df[metric] = (ranks * 100).round(0)
        
    return result_df
