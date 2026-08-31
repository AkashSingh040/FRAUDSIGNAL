import os
import json
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, 'ml_model_experimentation', 'random_forest')

def test_inference():
    print("Loading artifacts...")
    model_path = os.path.join(OUTPUT_DIR, 'rf_model.pkl')
    prep_path = os.path.join(OUTPUT_DIR, 'rf_preprocessor.pkl')
    feat_path = os.path.join(OUTPUT_DIR, 'rf_features.json')
    thresh_path = os.path.join(OUTPUT_DIR, 'rf_threshold.json')
    
    model = joblib.load(model_path)
    preprocessor = joblib.load(prep_path)
    imputer = preprocessor['imputer']
    freq_maps = preprocessor['freq_maps']
    
    with open(feat_path, 'r') as f:
        features = json.load(f)
        
    with open(thresh_path, 'r') as f:
        threshold = json.load(f)['optimal_threshold']
        
    # Create a mock raw transaction similar to what backend receives
    mock_tx = {
        'TransactionAmt': 150.0,
        'LogTransactionAmt': np.log1p(150.0),
        'hour': 14,
        'day': 100,
        'card1': 1000,
        'card2': 200,
        'card3': 150,
        'card4': 'visa',
        'card5': 226,
        'card6': 'credit',
        'addr1': 315,
        'addr2': 87,
        'dist1': 10,
        'ProductCD': 'W',
        'P_emaildomain': 'gmail.com',
        'R_emaildomain': 'missing'
    }
    # Add dummy V features
    for i in range(1, 15):
        mock_tx[f'V{i}'] = 0.0
        
    print("Processing transaction...")
    
    # Apply freq encoding
    for col, mapping in freq_maps.items():
        val = mock_tx.get(col)
        mock_tx[f'{col}_count'] = mapping.get(val, 0.0)
        
    # Create DataFrame in exact feature order
    df = pd.DataFrame([mock_tx], columns=features)
    
    # Convert anything missing to NaN (handled by imputer)
    df = df.fillna(np.nan)
    
    # Impute
    df_imp = pd.DataFrame(imputer.transform(df), columns=df.columns)
    
    print("Running inference...")
    prob = model.predict_proba(df_imp)[0][1]
    
    print("\n--- INFERENCE RESULT ---")
    print(f"Fraud Probability: {prob:.4f}")
    print(f"Threshold:         {threshold:.4f}")
    print(f"ML Prediction:     {'FRAUD' if prob >= threshold else 'LEGITIMATE'}")
    
if __name__ == "__main__":
    test_inference()
