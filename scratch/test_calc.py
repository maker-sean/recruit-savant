import pandas as pd
import numpy as np
from processing import calculate_percentiles

def test_calculation():
    # Create dummy data
    data = {
        'Name': ['A', 'B', 'C', 'D', 'E'],
        'ExitVelocity': [100, 90, 80, 70, np.nan], # Higher is better
        'Strikeouts': [10, 20, 30, 40, 50],      # Lower is better (K%)
        'SwingLength': [6.0, 6.5, 7.0, 7.5, 8.0] # Lower is better
    }
    df = pd.DataFrame(data)
    
    mapping = {
        'Player Name': 'Name',
        'Max EV': 'ExitVelocity',
        'K%': 'Strikeouts',
        'Swing Length': 'SwingLength'
    }
    
    print("Input Data:")
    print(df)
    
    results = calculate_percentiles(df, mapping)
    
    print("\nCalculated Percentiles:")
    print(results[['Player Name', 'Max EV', 'K%', 'Swing Length']])
    
    # Assertions
    # Swing Length: A(6.0) is lowest -> Highest Rank (100). E(8.0) is highest -> Lowest Rank (20).
    
    row_a = results[results['Player Name'] == 'A'].iloc[0]
    assert row_a['Swing Length'] == 100.0, f"Expected 100 for Swing Length 6.0, got {row_a['Swing Length']}"
    
    row_e = results[results['Player Name'] == 'E'].iloc[0]
    assert row_e['Swing Length'] == 20.0, f"Expected 20 for Swing Length 8.0, got {row_e['Swing Length']}"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_calculation()
