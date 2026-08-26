import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, precision_recall_curve
import joblib

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")
TRAIN_TRANSACTION_PATH = os.path.join(DATA_DIR, "train_transaction.csv")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fraud_model.pkl")

# We will save plots to the same artifacts directory so the agent can embed them
CM_PLOT_PATH = os.path.join(ARTIFACTS_DIR, "confusion_matrix.png")
ROC_PLOT_PATH = os.path.join(ARTIFACTS_DIR, "roc_curve.png")
PR_PLOT_PATH = os.path.join(ARTIFACTS_DIR, "pr_curve.png")

def main():
    print("Loading model...")
    model = joblib.load(MODEL_PATH)
    
    print("Loading dataset...")
    df = pd.read_csv(TRAIN_TRANSACTION_PATH)
    
    # We must use the exact same features and split as training to evaluate properly
    # Recreate the available features logic
    numeric_features = ['TransactionAmt', 'card1', 'card2', 'card3', 'card5', 'addr1', 'addr2', 'dist1']
    categorical_features = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain']
    numeric_features += [f'V{i}' for i in range(1, 11)]
    features = numeric_features + categorical_features
    available_features = [f for f in features if f in df.columns]
    
    X = df[available_features]
    y = df['isFraud']
    
    print("Splitting dataset...")
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Predicting...")
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Default threshold is 0.5
    y_pred = (y_prob >= 0.5).astype(int)
    
    print("Generating Classification Report:")
    report = classification_report(y_test, y_pred)
    print(report)
    
    # Plot Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Legitimate', 'Fraud'], 
                yticklabels=['Legitimate', 'Fraud'])
    plt.title('Confusion Matrix (Threshold = 0.5)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(CM_PLOT_PATH)
    plt.close()
    print(f"Saved confusion matrix to {CM_PLOT_PATH}")
    
    # Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    plt.savefig(ROC_PLOT_PATH)
    plt.close()
    print(f"Saved ROC curve to {ROC_PLOT_PATH}")
    
    # Plot Precision-Recall Curve
    precision, recall, thresholds = precision_recall_curve(y_test, y_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='purple', lw=2)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.savefig(PR_PLOT_PATH)
    plt.close()
    print(f"Saved PR curve to {PR_PLOT_PATH}")

if __name__ == "__main__":
    main()
