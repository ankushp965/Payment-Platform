import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Ledger Service", version="1.0.0")

# Database configuration from Environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ledger_db")

# SQLAlchemy setup with pool_pre_ping for resilient connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Transaction Table Model
class TransactionRecord(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)

# Auto-create table if not exists (for demo simplicity)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Database connection pending or failed on startup: {e}")

# Prometheus Metrics
LEDGER_OPERATIONS = Counter(
    "ledger_operations_total",
    "Total ledger transactions recorded",
    ["status"]
)
REQUEST_LATENCY = Histogram(
    "ledger_request_duration_seconds",
    "Ledger service latency in seconds",
    ["endpoint"]
)

# Pydantic Schemas
class LedgerEntryRequest(BaseModel):
    payment_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    account_id: str = Field(..., example="ACC-98765")
    amount: float = Field(..., gt=0, example=150.00)
    currency: str = Field(default="USD", example="USD")

class LedgerEntryResponse(BaseModel):
    status: str
    payment_id: str
    recorded_at: datetime

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    if request.url.path != "/metrics":
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "ledger", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/ledger", response_model=LedgerEntryResponse)
async def record_transaction(entry: LedgerEntryRequest):
    db = SessionLocal()
    try:
        record = TransactionRecord(
            payment_id=entry.payment_id,
            account_id=entry.account_id,
            amount=entry.amount,
            currency=entry.currency
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        LEDGER_OPERATIONS.labels(status="success").inc()
        return LedgerEntryResponse(
            status="RECORDED",
            payment_id=record.payment_id,
            recorded_at=record.created_at
        )
    except Exception as ex:
        db.rollback()
        LEDGER_OPERATIONS.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=f"Database ledger error: {str(ex)}")
    finally:
        db.close()