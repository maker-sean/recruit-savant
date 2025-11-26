import os
from flask import Flask, render_template, request, redirect, url_for, session
from processing import load_data, calculate_percentiles, TARGET_METRICS
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
        # Look for "player", "name", "batter"
        for col in columns:
            norm_col = normalize(col)
            if 'player' in norm_col or 'name' in norm_col or 'batter' in norm_col:
                suggested_mapping['Player Name'] = col
                break
        
        # 2. Map Target Metrics
        for target in TARGET_METRICS:
            norm_target = normalize(target)
            best_match = None
            
            for col in columns:
                norm_col = normalize(col)
                # Exact normalized match
                if norm_target == norm_col:
                    best_match = col
                    break
                # Partial match (e.g. "Exit Velocity" for "Max EV" -> "maxev" in "exitvelocity" NO. "maxev" in "maxexitvelocity" YES)
                # Let's try simple containment both ways
                if norm_target in norm_col or norm_col in norm_target:
                    # Prioritize exact matches or better partials? 
                    # For now, first found.
                    # Special case for K% vs Strikeouts
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
        
    results = calculate_percentiles(df, mapping)
    
    # Convert to list of dicts for template
    # Replace NaN with "N/A" for display
    results_data = results.fillna('N/A').to_dict(orient='records')
    
    return render_template('results.html', players=results_data, metrics=TARGET_METRICS)

if __name__ == '__main__':
    app.run(debug=True)
