import requests
import json
import time
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
import psutil

# Get current process
process = psutil.Process(os.getpid())

def print_mem(stage):
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory ({stage}): {mem_mb:.2f} MB")
    return mem_mb

print("================ INFERENCE & MEMORY TEST ================")
mem_start = print_mem("Startup")

# Load model locally to test size overhead
print("\nLoading model internally to measure overhead...")
from app.risk.model_loader import model_loader
mem_model = print_mem("After Model Load")
print(f"Model Load Memory Overhead: {mem_model - mem_start:.2f} MB")

# Test actual API Endpoint (ensure backend is running)
print("\nTesting FastAPI Endpoint...")
API_URL = "http://127.0.0.1:8000/api/v1/risk/score"
test_tx = {
    "transaction_id": "tx_rigorous_test",
    "merchant_id": "merch_1",
    "customer_id": "cust_1",
    "payment_method": "card",
    "amount": 999.99,
    "currency": "USD",
    "user_id": "usr_test123",
    "timestamp": "2024-10-31T23:59:59Z",
    "metadata": {
        "card_bin": 4444,
        "card_brand": "visa",
        "card_type": "credit",
        "email_domain": "gmail.com"
    }
}

try:
    response = requests.post(API_URL, json=test_tx, timeout=5)
    data = response.json()
    
    print("\nAPI Response:")
    print(json.dumps(data, indent=2))
    
    # Assertions
    assert 0 <= data["risk_score"] <= 100, "Risk score must be between 0 and 100"
    
    for sig in data.get("signals", []):
        if sig["source"] == "model":
            prob = sig["evidence"]["model_probability"]
            assert 0 <= prob <= 1, "Model probability must be between 0 and 1"
            print(f"\nAssertion Passed: Probability ({prob}) is bound between 0 and 1.")
            break
            
    # Verify model status
    status_resp = requests.get("http://127.0.0.1:8000/api/v1/risk/status")
    status = status_resp.json()
    
    print("\nAPI Model Status:")
    print(f"Version: {status.get('version')}")
    print(f"Threshold: {status.get('threshold')}")
    assert status.get("threshold") is not None, "Threshold should be loaded from config"
    
except Exception as e:
    print(f"API Error: {e}")
