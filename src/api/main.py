"""
FastAPI application entry point.
Week 3 deliverable — loads .env, mounts routes, adds MITRE attribution header.
"""
import logging
import os
from pathlib import Path
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from src.api.routes.alerts import router as alerts_router
from src.api.routes.evaluate import router as evaluate_router
from src.api.routes.rag import router as rag_router
from src.api.routes.taxonomy import router as taxonomy_router

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

app = FastAPI(
    title="Security Alert → ATT&CK Inference API",
    description="Advisory tagging only. Not autonomous SOC action.",
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

@app.middleware("http")
async def add_trace_headers(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied_request_id
        if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
        else str(uuid.uuid4())
    )
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-MITRE-ATTaCK-Version"] = "enterprise-attack-19.1"
    response.headers["X-Request-ID"] = request_id
    logging.getLogger("security_alert.api").info(
        "request method=%s path=%s status=%s latency_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
        request_id,
    )
    return response

app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(evaluate_router, tags=["evaluation"])
app.include_router(rag_router, prefix="/rag", tags=["rag"])
app.include_router(taxonomy_router, prefix="/taxonomy", tags=["taxonomy"])

@app.get("/")
async def health():
    return {"status": "ok", "stix_version": "19.1"}


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def analyst_ui():
    return HTMLResponse((PROJECT_ROOT / "ui" / "index.html").read_text(encoding="utf-8"))
