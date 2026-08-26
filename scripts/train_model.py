import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json
import time
import psutil
from datetime import datetime
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, auc, 
    precision_recall_curve, average_precision_score, precision_score, 
    recall_score, f1_score
)
# For baseline comparison
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")
EVAL_DIR = os.path.join(ARTIFACTS_DIR, "evaluation")
TRAIN_TRANSACTION_PATH = os.path.join(DATA_DIR, "train_transaction.csv")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fraud_model.pkl")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
THRESHOLD_CONFIG_PATH = os.path.join(ARTIFACTS_DIR, "threshold_config.json")

os.makedirs(EVAL_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv(TRAIN_TRANSACTION_PATH)
    return df

def feature_engineering(df):
    df['day'] = np.floor(df['TransactionDT'] / (3600 * 24)).astype(int)
    df['hour'] = np.floor((df['TransactionDT'] % (3600 * 24)) / 3600).astype(int)
    df['LogTransactionAmt'] = np.log1p(df['TransactionAmt'])
    return df

def get_feature_lists():
    numeric_features = [
        'TransactionAmt', 'LogTransactionAmt', 'hour', 'day',
        'card1', 'card2', 'card3', 'card5', 'addr1', 'addr2', 'dist1'
    ]
    numeric_features += [f'V{i}' for i in range(1, 15)]
    categorical_features = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain']
    freq_features = ['card1_count', 'card2_count', 'addr1_count', 'P_emaildomain_count']
    return numeric_features, categorical_features, freq_features

def apply_frequency_encoding(df_train, df_val, df_test, cols):
    df_train_out = df_train.copy()
    df_val_out = df_val.copy()
    df_test_out = df_test.copy()
    
    freq_maps = {}
    for col in cols:
        freq = df_train[col].value_counts(dropna=False, normalize=True).to_dict()
        freq_maps[col] = freq
        
        df_train_out[f'{col}_count'] = df_train[col].map(freq).fillna(0)
        df_val_out[f'{col}_count'] = df_val[col].map(freq).fillna(0)
        df_test_out[f'{col}_count'] = df_test[col].map(freq).fillna(0)
        
    return df_train_out, df_val_out, df_test_out, freq_maps

def print_split_stats(name, df):
    min_time = df['TransactionDT'].min() / (3600*24)
    max_time = df['TransactionDT'].max() / (3600*24)
    fraud_cnt = df['isFraud'].sum()
    total = len(df)
    prev = fraud_cnt / total if total > 0 else 0
    print(f"--- {name} Split ---")
    print(f"Time Range (days): {min_time:.1f} to {max_time:.1f}")
    print(f"Total Transactions: {total}")
    print(f"Fraud Count: {fraud_cnt}")
    print(f"Fraud Prevalence: {prev:.2%}\n")

def train_baseline(train_df, test_df, num_cols, cat_cols):
    """Trains the old HistGradientBoosting baseline for rigorous comparison on the exact same test set."""
    print("Training old baseline for comparison...")
    # Baseline only used a subset of features
    base_num = ['TransactionAmt', 'card1', 'card2', 'card3', 'card5', 'addr1', 'addr2', 'dist1']
    base_num += [f'V{i}' for i in range(1, 11)]
    base_cat = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain']
    
    num_trans = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
    cat_trans = Pipeline(steps=[('imputer', SimpleImputer(strategy='constant', fill_value='missing')), ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))])
    
    preprocessor = ColumnTransformer(transformers=[('num', num_trans, base_num), ('cat', cat_trans, base_cat)])
    model = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', HistGradientBoostingClassifier(max_iter=100, random_state=42))])
    
    # Fill NAs to simulate old process
    train_x = train_df.copy()
    test_x = test_df.copy()
    
    model.fit(train_x[base_num + base_cat], train_x['isFraud'])
    y_prob = model.predict_proba(test_x[base_num + base_cat])[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    
    fpr, tpr, _ = roc_curve(test_x['isFraud'], y_prob)
    roc_auc = auc(fpr, tpr)
    pr_auc = average_precision_score(test_x['isFraud'], y_prob)
    
    return {
        "ROC-AUC": roc_auc,
        "PR-AUC": pr_auc,
        "Precision": precision_score(test_x['isFraud'], y_pred, zero_division=0),
        "Recall": recall_score(test_x['isFraud'], y_pred),
        "F1": f1_score(test_x['isFraud'], y_pred)
    }

def train_and_evaluate():
    print("Loading data...")
    df = load_data()
    df = df.sort_values('TransactionDT').reset_index(drop=True)
    df = feature_engineering(df)
    
    # Split 70% Train, 15% Val, 15% Test
    idx_train = int(len(df) * 0.70)
    idx_val = int(len(df) * 0.85)
    
    train_df = df.iloc[:idx_train].copy()
    val_df = df.iloc[idx_train:idx_val].copy()
    test_df = df.iloc[idx_val:].copy()
    
    print("\n================ SPLIT VERIFICATION ================")
    print_split_stats("Train", train_df)
    print_split_stats("Validation", val_df)
    print_split_stats("Test", test_df)
    print("====================================================\n")
    
    num_cols, cat_cols, freq_cols = get_feature_lists()
    
    # Train baseline on exact same split for comparison
    baseline_metrics = train_baseline(train_df, test_df, num_cols, cat_cols)
    
    # Apply Frequency Encoding
    train_df, val_df, test_df, freq_maps = apply_frequency_encoding(
        train_df, val_df, test_df, ['card1', 'card2', 'addr1', 'P_emaildomain']
    )
    
    for col in cat_cols:
        train_df[col] = train_df[col].astype(str).fillna('missing').astype('category')
        val_df[col] = val_df[col].astype(str).fillna('missing').astype('category')
        test_df[col] = test_df[col].astype(str).fillna('missing').astype('category')
        
    features = num_cols + cat_cols + freq_cols
    available_features = [f for f in features if f in train_df.columns]
    
    X_train = train_df[available_features].copy()
    y_train = train_df['isFraud']
    X_val = val_df[available_features].copy()
    y_val = val_df['isFraud']
    X_test = test_df[available_features].copy()
    y_test = test_df['isFraud']
    
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos = 10.0 # Bounded to preserve gradient stability
    
    clf = lgb.LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=7,
        num_leaves=64,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        metric='auc',
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting New LightGBM model...")
    clf.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )
    
    # ==========================================
    # VALIDATION: Optimize Threshold
    # ==========================================
    print("\nOptimizing threshold on VALIDATION SET...")
    y_val_prob = clf.predict_proba(X_val)[:, 1]
    
    best_f1 = 0
    optimal_thresh = 0.5
    for thresh in np.arange(0.05, 0.95, 0.05):
        y_val_pred = (y_val_prob >= thresh).astype(int)
        f1 = f1_score(y_val, y_val_pred)
        if f1 > best_f1:
            best_f1 = f1
            optimal_thresh = thresh
            
    print(f"Selected Optimal Threshold from Validation Set: {optimal_thresh:.2f}")
    
    # ==========================================
    # TEST: Unbiased Evaluation
    # ==========================================
    print("\nEvaluating on TEST SET...")
    y_test_prob = clf.predict_proba(X_test)[:, 1]
    
    fpr_curve, tpr_curve, _ = roc_curve(y_test, y_test_prob)
    test_roc_auc = auc(fpr_curve, tpr_curve)
    test_pr_auc = average_precision_score(y_test, y_test_prob)
    
    # Generate Threshold Comparison Table on Test set
    thresholds = [0.10, 0.20, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80]
    metrics_list = []
    
    print(f"{'Threshold':<10} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10} | {'Flagged':<10}")
    print("-" * 70)
    for t in thresholds:
        yp = (y_test_prob >= t).astype(int)
        p = precision_score(y_test, yp, zero_division=0)
        r = recall_score(y_test, yp)
        f = f1_score(y_test, yp)
        tn, fp, fn, tp = confusion_matrix(y_test, yp).ravel()
        fpr_val = fp / (fp + tn) if (fp+tn) > 0 else 0
        metrics_list.append({"Threshold": t, "Precision": p, "Recall": r, "F1": f, "FPR": fpr_val, "Flagged": fp+tp})
        print(f"{t:<10.2f} | {p:<10.4f} | {r:<10.4f} | {f:<10.4f} | {fpr_val:<10.4f} | {fp+tp:<10}")
        
    df_metrics = pd.DataFrame(metrics_list)
    df_metrics.to_csv(os.path.join(EVAL_DIR, "threshold_metrics.csv"), index=False)
    
    # Exact metrics at optimal threshold
    yp_opt = (y_test_prob >= optimal_thresh).astype(int)
    opt_p = precision_score(y_test, yp_opt, zero_division=0)
    opt_r = recall_score(y_test, yp_opt)
    opt_f = f1_score(y_test, yp_opt)
    tn, fp, fn, tp = confusion_matrix(y_test, yp_opt).ravel()
    opt_fpr = fp / (fp + tn)
    opt_fnr = fn / (fn + tp)
    
    print(f"\n================ FINAL MODEL COMPARISON (TEST SET) ================")
    print(f"{'Metric':<20} | {'Old Baseline':<20} | {'New LightGBM':<20}")
    print("-" * 65)
    print(f"{'ROC-AUC':<20} | {baseline_metrics['ROC-AUC']:<20.4f} | {test_roc_auc:<20.4f}")
    print(f"{'PR-AUC':<20} | {baseline_metrics['PR-AUC']:<20.4f} | {test_pr_auc:<20.4f}")
    print(f"{'Precision':<20} | {baseline_metrics['Precision']:<20.4f} | {opt_p:<20.4f}")
    print(f"{'Recall':<20} | {baseline_metrics['Recall']:<20.4f} | {opt_r:<20.4f}")
    print(f"{'F1':<20} | {baseline_metrics['F1']:<20.4f} | {opt_f:<20.4f}")
    print("===================================================================\n")
    
    print(f"Metrics at Optimal Threshold ({optimal_thresh:.2f}):")
    print(f"False Positive Rate: {opt_fpr:.4f}")
    print(f"False Negative Rate: {opt_fnr:.4f}")
    print(f"Fraud transactions flagged (TP): {tp}")
    print(f"Legitimate transactions flagged (FP): {fp}")

    # Visualizations
    precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_test_prob)
    plt.figure(figsize=(8,6))
    plt.plot(recall_curve, precision_curve, label=f'PR AUC = {test_pr_auc:.3f}')
    plt.title('Precision-Recall Curve (Test Set)')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.legend()
    plt.savefig(os.path.join(EVAL_DIR, "precision_recall_curve.png"))
    plt.close()
    
    # Save Model Artifacts
    model_artifact = {
        "model": clf,
        "features": available_features,
        "cat_cols": [c for c in cat_cols if c in available_features],
        "freq_maps": freq_maps
    }
    joblib.dump(model_artifact, MODEL_PATH)
    
    metadata = {
        "model_name": "FraudSignal-M1-LightGBM",
        "model_version": "v1.2-rigorous",
        "dataset": "IEEE-CIS Fraud Detection",
        "trained_at": datetime.utcnow().isoformat(),
        "roc_auc": float(test_roc_auc),
        "pr_auc": float(test_pr_auc),
        "selected_threshold": float(optimal_thresh),
        "precision": float(opt_p),
        "recall": float(opt_r),
        "f1": float(opt_f),
        "feature_count": len(available_features),
        "model_type": "LightGBM"
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
        
    with open(THRESHOLD_CONFIG_PATH, "w") as f:
        json.dump({"optimal_threshold": float(optimal_thresh)}, f, indent=2)
        
    print("\nArtifact Sizes:")
    print(f"Model (.pkl): {os.path.getsize(MODEL_PATH) / 1024 / 1024:.2f} MB")
    print(f"Config (.json): {os.path.getsize(THRESHOLD_CONFIG_PATH)} bytes")
    print(f"Metadata (.json): {os.path.getsize(METADATA_PATH)} bytes")
    
if __name__ == "__main__":
    train_and_evaluate()
