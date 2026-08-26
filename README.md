# FraudSignal

**Evidence-backed payment risk intelligence and AI investigation.**

FraudSignal detects suspicious payment behavior, calculates an explainable risk score, identifies the evidence behind the risk, investigates suspicious cases using AI, and presents the result to a merchant or risk investigator in a modern React Command Center.

## Architecture

1. **Transaction Normalization**: Consumes transactions from Razorpay (or a Simulator) and normalizes them into a standard schema.
2. **Hybrid Risk Engine**: Combines an ML model (trained on the IEEE-CIS Fraud Detection dataset) with deterministic rules (e.g., velocity checks, amount anomalies).
3. **AI Investigation Service**: Generates structured, evidence-backed investigation reports explaining the risk signals and recommending human action.
4. **Command Center**: A React dashboard for risk investigators to review cases, examine evidence, and make final decisions.

## Prerequisites

- Python 3.13+
- Node.js 18+
- MongoDB (running on `localhost:27017` or via Docker)

## Setup

1. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your details (LLM API key, Razorpay keys).

2. **MongoDB**:
   Ensure MongoDB is installed and running locally on port 27017, or update the `MONGODB_URI` in your `.env` file to point to your MongoDB Atlas cluster if deploying to Render.

3. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **ML Training** (Optional if dataset is available):
   Place `train_transaction.csv` and `train_identity.csv` in `data/raw/`.
   ```bash
   pip install -r ml/requirements.txt
   python scripts/train_model.py
   python scripts/evaluate_model.py
   ```

## Demo Flow

- Navigate to `http://localhost:5173` (Frontend).
- Open the **Simulator** page and submit a **HIGH RISK** transaction.
- Go to **Investigations** or **Transactions** to see the newly generated case.
- Review the AI investigation reasoning, evidence, and apply a decision (e.g., **BLOCK**).
# FRAUDSIGNAL
