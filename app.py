import os
from flask import Flask, render_template, request, redirect, url_for, session
from processing import load_data, calculate_percentiles, calculate_synthetic_xwoba, TARGET_METRICS
import pandas as pd

app = Flask(__name__)
app.secret_key = 'recruit_savant_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        session['filename'] = file.filename
        
        # Load just to get columns
        # We re-open it to ensure it's readable
        with open(filepath, 'rb') as f:
            # We need to wrap it in a way load_data expects if it expects a FileStorage, 
            # but load_data currently expects FileStorage. 
            # Let's refactor load_data slightly or just use pd.read_... directly here for columns.
            # Actually, let's make load_data accept a path or file-like object.
            # For now, I'll just read it here quickly.
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, nrows=0) # Just read header
            else:
                df = pd.read_excel(filepath, nrows=0)
                
        columns = df.columns.tolist()
        
        # Auto-Mapping Logic
        suggested_mapping = {}
        
        # Helper to normalize strings for comparison
        def normalize(s):
            return str(s).lower().replace(' ', '').replace('_', '').replace('.', '').replace('%', '')

        # 1. Map Player Name
        # Priority list for Player Name
        player_name_candidates = ['playerfullname', 'battername', 'playername', 'batter', 'player']
        
        for candidate in player_name_candidates:
            found = False
            for col in columns:
                norm_col = normalize(col)
                if candidate == norm_col:
                    suggested_mapping['Player Name'] = col
                    found = True
                    break
            if found:
                break
        
        # Fallback if no exact match found, look for partials
        if 'Player Name' not in suggested_mapping:
            for col in columns:
                norm_col = normalize(col)
                if 'player' in norm_col or 'name' in norm_col or 'batter' in norm_col:
                    suggested_mapping['Player Name'] = col
                    break
        
        # 2. Map Target Metrics
        for target in TARGET_METRICS:
            norm_target = normalize(target)
            best_match = None
            
            # Special handling for Max EV
            if target == 'Max EV':
                max_ev_candidates = ['maxexitvelocity', 'maxexitvel', 'maxev', 'exitvelocity', 'exitvel', 'ev']
                for candidate in max_ev_candidates:
                    for col in columns:
                        norm_col = normalize(col)
                        if candidate == norm_col:
                            best_match = col
                            break
                    if best_match:
                        break
            
            if not best_match:
                for col in columns:
                    norm_col = normalize(col)
                    # Exact normalized match
                    if norm_target == norm_col:
                        best_match = col
                        break
                    # Partial match
                    if norm_target in norm_col or norm_col in norm_target:
                        if target == 'K%' and 'strikeout' in norm_col:
                            best_match = col
                            break
                        if target == 'BB%' and 'walk' in norm_col:
                            best_match = col
                            break
                        best_match = col
            
            if best_match:
                suggested_mapping[target] = best_match

        return render_template('mapping.html', columns=columns, targets=TARGET_METRICS, suggested_mapping=suggested_mapping)

@app.route('/calculate', methods=['POST'])
def calculate():
    filename = session.get('filename')
    if not filename:
        return redirect(url_for('index'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Re-load full data
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
        
    # Get mapping from form
    mapping = {}
    # We expect inputs like name="map_Max EV"
    for metric in TARGET_METRICS:
        val = request.form.get(f'map_{metric}')
        if val and val != 'None':
            mapping[metric] = val
            
    # Also get Player Name mapping
    player_col = request.form.get('map_Player Name')
    if player_col:
        mapping['Player Name'] = player_col
        
    # Save mapping to session for advanced analysis
    session['mapping'] = mapping
    
    results = calculate_percentiles(df, mapping)
    
    # Convert to list of dicts for template
    # Replace NaN with "N/A" for display
    results_data = results.fillna('N/A').to_dict(orient='records')
    
    return render_template('results.html', players=results_data, metrics=TARGET_METRICS)

@app.route('/advanced_analysis', methods=['GET', 'POST'])
def advanced_analysis():
    filename = session.get('filename')
    mapping = session.get('mapping')
    
    if not filename or not mapping:
        return redirect(url_for('index'))
        
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
        
    # Default weights
    default_weights = {
        'w_bb': 0.7,
        'w_k': 0.7,
        'w_power': 0.25,
        'w_contact': 0.2,
        'base_woba': 0.280
    }
    
    # Get weights from session or defaults
    weights = session.get('weights', default_weights)
    
    # If POST, update weights from form
    if request.method == 'POST':
        try:
            weights['w_bb'] = float(request.form.get('w_bb', weights['w_bb']))
            weights['w_k'] = float(request.form.get('w_k', weights['w_k']))
            weights['w_power'] = float(request.form.get('w_power', weights['w_power']))
            weights['w_contact'] = float(request.form.get('w_contact', weights['w_contact']))
            weights['base_woba'] = float(request.form.get('base_woba', weights['base_woba']))
            session['weights'] = weights
        except ValueError:
            # Handle invalid input gracefully (keep old weights)
            pass
        
    # Calculate Synthetic xwOBA
    syn_xwoba = calculate_synthetic_xwoba(df, mapping, weights)
    
    # Prepare data for display
    # Create a result DF with Player Name and Syn xwOBA
    player_col = mapping.get('Player Name')
    if player_col and player_col in df.columns:
        players = df[player_col]
    else:
        players = df.index.astype(str)
        
    results_df = pd.DataFrame({
        'Player Name': players,
        'Synthetic xwOBA': syn_xwoba.round(3)
    })
    
    # Also add the components for transparency AND their percentiles for coloring
    def get_col(metric):
        return mapping.get(metric)
        
    # We need to calculate percentiles for these specific metrics to do the color coding
    # Re-use calculate_percentiles logic or call it?
    # Calling calculate_percentiles gives us everything. Let's do that and merge.
    
    full_percentiles = calculate_percentiles(df, mapping)
    
    for metric in ['BB%', 'K%', 'Max EV', 'Contact%']:
        col = get_col(metric)
        if col and col in df.columns:
            # Raw Value
            results_df[metric] = df[col]
            # Percentile Value (for coloring)
            if metric in full_percentiles.columns:
                results_df[f'{metric}_pct'] = full_percentiles[metric]
            else:
                results_df[f'{metric}_pct'] = 0 # Default if missing
        else:
            results_df[metric] = 'N/A'
            results_df[f'{metric}_pct'] = 'N/A'
            
    results_data = results_df.to_dict(orient='records')
    
    return render_template('advanced_results.html', players=results_data, weights=weights)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

