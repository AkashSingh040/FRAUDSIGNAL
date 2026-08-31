import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from sklearn.impute import SimpleImputer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
OUTPUT_DIR = os.path.join(BASE_DIR, 'ml_model_experimentation', 'random_forest')

def load_data():
    trans = pd.read_csv(os.path.join(DATA_DIR, 'train_transaction.csv'))
    id_df = pd.read_csv(os.path.join(DATA_DIR, 'train_identity.csv'))
    df = pd.merge(trans, id_df, on='TransactionID', how='left')
    return df

def feature_engineering(df):
    df['day'] = np.floor(df['TransactionDT'] / (3600 * 24)).astype(int)
    df['hour'] = np.floor((df['TransactionDT'] % (3600 * 24)) / 3600).astype(int)
    df['LogTransactionAmt'] = np.log1p(df['TransactionAmt'])
    return df

def main():
    df = load_data()
    df = df.sort_values('TransactionDT').reset_index(drop=True)
    df = feature_engineering(df)
    
    idx_train = int(len(df) * 0.60)
    idx_val = int(len(df) * 0.80)
    
    train_df = df.iloc[:idx_train].copy()
    val_df = df.iloc[idx_train:idx_val].copy()
    test_df = df.iloc[idx_val:].copy()
    
    print("\n--- SPLIT STATISTICS ---")
    print(f"Train Size: {len(train_df)} | Fraud Count: {train_df['isFraud'].sum()} | Prev: {train_df['isFraud'].mean():.4f}")
    print(f"Val Size:   {len(val_df)} | Fraud Count: {val_df['isFraud'].sum()} | Prev: {val_df['isFraud'].mean():.4f}")
    print(f"Test Size:  {len(test_df)} | Fraud Count: {test_df['isFraud'].sum()} | Prev: {test_df['isFraud'].mean():.4f}")
    
    numeric_features = [
        'TransactionAmt', 'LogTransactionAmt', 'hour', 'day',
        'card3', 'card5', 'addr2', 'dist1'
    ] + [f'V{i}' for i in range(1, 15)]
    
    freq_encoding_cols = ['card1', 'card2', 'addr1', 'ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain']
    
    freq_maps = {}
    for col in freq_encoding_cols:
        freq = train_df[col].value_counts(dropna=False, normalize=True).to_dict()
        freq_maps[col] = freq
        
        train_df[f'{col}_count'] = train_df[col].map(freq).fillna(0)
        val_df[f'{col}_count'] = val_df[col].map(freq).fillna(0)
        test_df[f'{col}_count'] = test_df[col].map(freq).fillna(0)
        
    features = numeric_features + [f'{c}_count' for c in freq_encoding_cols]
    
    X_train = train_df[features].copy()
    y_train = train_df['isFraud']
    X_val = val_df[features].copy()
    y_val = val_df['isFraud']
    X_test = test_df[features].copy()
    y_test = test_df['isFraud']
    
    imputer = SimpleImputer(strategy='median')
    X_train_imp = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns)
    X_val_imp = pd.DataFrame(imputer.transform(X_val), columns=X_val.columns)
    X_test_imp = pd.DataFrame(imputer.transform(X_test), columns=X_test.columns)
    
    seeds = [42, 123, 2026]
    
    print("\n--- STABILITY AUDIT ---")
    for s in seeds:
        print(f"\nTraining RF with Seed: {s} (class_weight='balanced', min_samples_leaf=1, n_estimators=200)")
        rf = RandomForestClassifier(
            n_estimators=200, 
            class_weight="balanced", 
            min_samples_leaf=1, 
            random_state=s, 
            n_jobs=-1
        )
        rf.fit(X_train_imp, y_train)
        
        y_val_prob = rf.predict_proba(X_val_imp)[:, 1]
        y_test_prob = rf.predict_proba(X_test_imp)[:, 1]
        
        pr_val = average_precision_score(y_val, y_val_prob)
        pr_test = average_precision_score(y_test, y_test_prob)
        
        print(f"Seed {s} -> Val PR-AUC: {pr_val:.6f}")
        print(f"Seed {s} -> Test PR-AUC: {pr_test:.6f}")

if __name__ == "__main__":
    main()
