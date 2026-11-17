import os
import time
import uuid
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Payment API", version="1.0.0")

# Service URLs from Environment (Service Discovery in K8s)
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8001")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://localhost:8002")
SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").lower() == "true"

# Prometheus Metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests handled by payment-api",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"]
)

class PaymentRequest(BaseModel):
    account_id: str = Field(..., example="ACC-98765")
    amount: float = Field(..., gt=0, example=150.00)
    currency: str = Field(default="USD", example="USD")

class PaymentResponse(BaseModel):
    payment_id: str
    account_id: str
    amount: float
    currency: str
    status: str
    ledger_status: str
    notification_status: str

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Exclude metrics endpoint itself from monitoring
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
        
    return response

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "payment-api", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/payments", response_model=PaymentResponse)
async def process_payment(payment: PaymentRequest):
    # Chaos / Canary Rollback injection trigger for later testing
    if SIMULATE_FAILURE:
        raise HTTPException(status_code=500, detail="Simulated payment processing failure!")

    payment_id = str(uuid.uuid4())

    # 1. Record transaction in Ledger Service
    ledger_status = "skipped"
    async with httpx.AsyncClient() as client:
        try:
            ledger_payload = {
                "payment_id": payment_id,
                "account_id": payment.account_id,
                "amount": payment.amount,
                "currency": payment.currency
            }
            ledger_res = await client.post(f"{LEDGER_URL}/api/v1/ledger", json=ledger_payload, timeout=2.0)
            ledger_status = "recorded" if ledger_res.status_code == 200 else f"failed_{ledger_res.status_code}"
        except Exception:
            ledger_status = "unavailable"

    # 2. Trigger notification
    notification_status = "skipped"
    async with httpx.AsyncClient() as client:
        try:
            notif_payload = {
                "payment_id": payment_id,
                "account_id": payment.account_id,
                "message": f"Payment of {payment.amount} {payment.currency} processed."
            }
            notif_res = await client.post(f"{NOTIFICATION_URL}/api/v1/notifications", json=notif_payload, timeout=2.0)
            notification_status = "sent" if notif_res.status_code == 200 else f"failed_{notif_res.status_code}"
        except Exception:
            notification_status = "unavailable"

    return PaymentResponse(
        payment_id=payment_id,
        account_id=payment.account_id,
        amount=payment.amount,
        currency=payment.currency,
        status="SUCCESS",
        ledger_status=ledger_status,
        notification_status=notification_status
    )