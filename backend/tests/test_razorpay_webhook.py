import pytest
from fastapi.testclient import TestClient
import hmac
import hashlib
import json
import os

from app.main import app
from unittest.mock import patch, MagicMock
from pymongo.errors import DuplicateKeyError

client = TestClient(app)

@pytest.fixture
def mock_env():
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_secret"
    yield
    del os.environ["RAZORPAY_WEBHOOK_SECRET"]

def generate_signature(payload: dict, secret: str) -> str:
    body = json.dumps(payload).encode('utf-8')
    return hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()

def test_missing_signature():
    response = client.post("/api/v1/razorpay/webhook", json={"event": "order.created"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing signature or secret"

def test_invalid_signature(mock_env):
    payload = {"event": "order.created"}
    headers = {"x-razorpay-signature": "invalid_sig_here"}
    response = client.post("/api/v1/razorpay/webhook", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"

def test_valid_order_created_ignored(mock_env):
    payload = {"event": "order.created"}
    sig = generate_signature(payload, "test_secret")
    headers = {"x-razorpay-signature": sig}
    
    # We use data=json.dumps(payload) instead of json=payload to ensure exact string matching for HMAC
    response = client.post("/api/v1/razorpay/webhook", data=json.dumps(payload), headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('app.api.routes.razorpay.process_transaction')
def test_valid_payment_captured_processed(mock_process_tx, mock_env):
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_123",
                    "amount": 50000,
                    "currency": "INR",
                    "email": "test@test.com",
                    "card": {"network": "Visa", "type": "credit"}
                }
            }
        }
    }
    sig = generate_signature(payload, "test_secret")
    headers = {"x-razorpay-signature": sig}
    
    # Mock successful async process_transaction
    async def mock_async_process(*args, **kwargs):
        return None
    mock_process_tx.side_effect = mock_async_process
    
    response = client.post("/api/v1/razorpay/webhook", data=json.dumps(payload), headers=headers)
    assert response.status_code == 200
    
    # process_transaction should be called via background task
    # fastapi test client executes background tasks immediately
    mock_process_tx.assert_called_once()
    
    # Check normalization
    tx_arg = mock_process_tx.call_args[0][0]
    assert tx_arg.transaction_id == "pay_123_payment.captured"
    assert tx_arg.amount == 500.0
    assert tx_arg.metadata["razorpay_event"] == "payment.captured"
    assert tx_arg.metadata["card_network"] == "Visa"

@patch('app.api.routes.razorpay.process_transaction')
def test_idempotency_duplicate_key_ignored(mock_process_tx, mock_env):
    payload = {
        "event": "payment.authorized",
        "payload": {"payment": {"entity": {"id": "pay_456", "amount": 100}}}
    }
    sig = generate_signature(payload, "test_secret")
    headers = {"x-razorpay-signature": sig}
    
    async def mock_duplicate_key(*args, **kwargs):
        raise DuplicateKeyError("E11000 duplicate key error")
    mock_process_tx.side_effect = mock_duplicate_key
    
    # This should return 200 OK despite the duplicate key error in the background
    response = client.post("/api/v1/razorpay/webhook", data=json.dumps(payload), headers=headers)
    assert response.status_code == 200
