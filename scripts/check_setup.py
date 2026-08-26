import os
import sys

def check_setup():
    print("Checking FraudSignal setup...")
    
    # Check dependencies
    print("\n--- Dependencies ---")
    try:
        import fastapi
        import motor
        import pandas
        import sklearn
        print("Required Python packages are installed.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        
    # Check dataset
    print("\n--- ML Dataset ---")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    tx_path = os.path.join(data_dir, "train_transaction.csv")
    if os.path.exists(tx_path):
        print("IEEE-CIS Fraud Detection dataset found.")
    else:
        print("IEEE-CIS Fraud Detection dataset NOT FOUND. System will run in rules-only fallback mode.")
        
    print("\nSetup check complete.")

if __name__ == "__main__":
    check_setup()
