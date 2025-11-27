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
    "Swing Length",
    "Contact%"
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

def clean_numeric_series(series):
    """
    Cleans a pandas Series to ensure it's numeric.
    Handles strings with %, mph, whitespace, etc.
    """
    # If already numeric, just coerce to handle mixed types if any
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce')
        
    # Convert to string, strip whitespace
    s = series.astype(str).str.strip()
    
    # Remove common units
    s = s.str.replace('%', '', regex=False)
    s = s.str.replace('mph', '', regex=False, case=False)
    s = s.str.replace('ft', '', regex=False, case=False)
    
    return pd.to_numeric(s, errors='coerce')

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
        
        # 2. Type Enforcement: Robust cleaning
        series = clean_numeric_series(df[user_col])
        
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

def calculate_synthetic_xwoba(df, mapping, weights=None):
    """
    Calculates a Synthetic xwOBA based on available metrics.
    Formula:
    Base (Default 0.280) 
    + (BB% * w_bb) 
    - (K% * w_k) 
    + ((Max EV - 75) / 35 * w_power) 
    + ((Contact% - 70) * w_contact)
    
    All inputs are expected to be 0-100 scale (e.g. 10.5 for 10.5%).
    """
    # Default weights
    if weights is None:
        weights = {
            'w_bb': 0.7,
            'w_k': 0.7,
            'w_power': 0.25,
            'w_contact': 0.2,
            'base_woba': 0.280
        }
        
    # Create a copy to avoid SettingWithCopy warnings on the original df
    res = pd.DataFrame(index=df.index)
    
    # Helper to get series or 0
    def get_series(metric_name):
        col = mapping.get(metric_name)
        if col and col in df.columns:
            return clean_numeric_series(df[col]).fillna(0)
        return pd.Series(0, index=df.index)

    bb_pct = get_series('BB%')
    k_pct = get_series('K%')
    max_ev = get_series('Max EV')
    contact_pct = get_series('Contact%') 
    
    # Formula components
    base_woba = float(weights.get('base_woba', 0.280))
    w_bb = float(weights.get('w_bb', 0.7))
    w_k = float(weights.get('w_k', 0.7))
    w_power = float(weights.get('w_power', 0.25))
    w_contact = float(weights.get('w_contact', 0.2))
    
    # BB Contribution
    bb_val = (bb_pct / 100.0) * w_bb
    
    # K Penalty
    k_val = (k_pct / 100.0) * w_k
    
    # Power: Max EV
    power_val = ((max_ev - 75) / 35.0) * w_power
    
    # Contact
    # Normalize to 0-1 scale: 70% = 0, 100% = 1
    contact_val = ((contact_pct - 70) / 30.0) * w_contact
    
    syn_xwoba = base_woba + bb_val - k_val + power_val + contact_val
    
    return syn_xwoba
