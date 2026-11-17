import time
import uuid
from datetime import datetime
from fastapi import FastAPI, Response, Request
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Notification Service", version="1.0.0")

# Prometheus Metrics
NOTIFICATIONS_TOTAL = Counter(
    "notifications_total",
    "Total customer notifications processed",
    ["channel", "status"]
)
REQUEST_LATENCY = Histogram(
    "notification_request_duration_seconds",
    "Notification service latency in seconds",
    ["endpoint"]
)

class NotificationRequest(BaseModel):
    payment_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")
    account_id: str = Field(..., example="ACC-98765")
    message: str = Field(..., example="Payment of 150.00 USD processed successfully.")
    channel: str = Field(default="sms", example="sms")

class NotificationResponse(BaseModel):
    status: str
    notification_id: str
    payment_id: str
    channel: str
    sent_at: datetime

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
    return {"status": "healthy", "service": "notification", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/notifications", response_model=NotificationResponse)
async def send_notification(payload: NotificationRequest):
    notif_id = str(uuid.uuid4())
    
    # In real production: AWS SNS, SES, or Twilio API call happens here.
    # Mocking successful dispatch:
    NOTIFICATIONS_TOTAL.labels(channel=payload.channel, status="delivered").inc()

    return NotificationResponse(
        status="SENT",
        notification_id=notif_id,
        payment_id=payload.payment_id,
        channel=payload.channel,
        sent_at=datetime.utcnow()
    )