from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.config import settings
import logging

# Ensure logging is configured
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FraudSignal API", description="Risk Intelligence and Investigation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "fraudsignal-api"}

from app.api.routes import risk, cases, dashboard, razorpay

app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(razorpay.router, prefix="/api/v1/razorpay", tags=["Razorpay"])

