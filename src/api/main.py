"""FastAPI application with explicit lifecycle and sandbox privacy defaults."""
import asyncio
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import hmac
import json
import logging
import os
from pathlib import Path
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from src.api import runtime
from src.api.routes.alerts import router as alerts_router
from src.api.routes.evaluate import router as evaluate_router
from src.api.routes.rag import router as rag_router
from src.api.routes.taxonomy import router as taxonomy_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
MAX_REQUEST_BYTES = 600_000


def error(status, code, message):
    return JSONResponse(status_code=status, content={"detail": {"code": code, "message": message}})


def create_app(*, snapshot_path=None, api_key=None, rate_limit=None, request_timeout=None):
    deployment = os.getenv("APP_ENV", "sandbox") == "deployment"
    key = api_key if api_key is not None else os.getenv("SECURITY_ALERT_API_KEY", "")
    limit = rate_limit if rate_limit is not None else int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    deadline = request_timeout if request_timeout is not None else float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000").split(",") if o.strip()]
    if "*" in origins or any(not o.startswith(("http://", "https://")) for o in origins):
        raise ValueError("CORS requires explicit HTTP(S) origins")
    if deployment and len(key) < 32:
        raise ValueError("Deployment requires a SECURITY_ALERT_API_KEY of at least 32 characters")
    if not 1 <= limit <= 10000 or not 0 < deadline <= 120:
        raise ValueError("Invalid rate limit or request deadline")

    @asynccontextmanager
    async def lifespan(application):
        application.state.retriever = None
        try:
            application.state.retriever = runtime.load_knowledge_base(Path(snapshot_path or runtime.SNAPSHOT_PATH))
        except (OSError, ValueError, KeyError, TypeError):
            logging.getLogger("security_alert.api").error("knowledge_base_unavailable")
        application.state.worker_slots = asyncio.Semaphore(4)
        application.state.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="alert-worker")
        application.state.rate_buckets = OrderedDict()
        try:
            yield
        finally:
            application.state.executor.shutdown(wait=False, cancel_futures=True)
            application.state.retriever = None

    application = FastAPI(title="Security Alert → ATT&CK Inference API",
        description="Advisory only. MITRE ATT&CK Enterprise 19.1. Analyst verification required.",
        version="0.3.0", lifespan=lifespan)

    @application.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # Pydantic errors include input and ValueError context by default.
        return error(422, "INVALID_REQUEST", "Request does not match the API contract.")

    @application.middleware("http")
    async def controls(request: Request, call_next):
        supplied = request.headers.get("X-Request-ID", "")
        server_trace_id = str(uuid.uuid4())
        request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else server_trace_id
        request.state.request_id = request_id
        started = time.monotonic()
        request.state.deadline = started + deadline

        async def dispatch():
            protected = request.url.path not in {"/", "/ui"} and request.method != "OPTIONS"
            if protected and key and not hmac.compare_digest(request.headers.get("X-API-Key", "").encode(), key.encode()):
                return error(401, "UNAUTHORIZED", "A valid API key is required.")
            if protected:
                buckets = getattr(application.state, "rate_buckets", None)
                if buckets is not None:
                    client = request.client.host if request.client else "unknown"
                    now = time.monotonic()
                    count, reset = buckets.get(client, (0, now + 60))
                    if now >= reset:
                        count, reset = 0, now + 60
                    if count >= limit:
                        response = error(429, "RATE_LIMITED", "Request quota exceeded.")
                        response.headers["Retry-After"] = str(max(1, int(reset - now)))
                        return response
                    buckets[client] = (count + 1, reset)
                    buckets.move_to_end(client)
                    if len(buckets) > 1024:
                        buckets.popitem(last=False)
            if request.method == "POST":
                chunks = []
                size = 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > MAX_REQUEST_BYTES:
                        return error(413, "REQUEST_TOO_LARGE", "Request body exceeds the allowed size.")
                    chunks.append(chunk)
                request._body = b"".join(chunks)
            return await call_next(request)

        try:
            response = await asyncio.wait_for(dispatch(), timeout=deadline)
        except TimeoutError:
            response = error(504, "INFERENCE_TIMEOUT", "Inference timed out. Human review is required.")
        except Exception:
            response = error(500, "INTERNAL_ERROR", "Request could not be completed.")
        response.headers["X-MITRE-ATTaCK-Version"] = "enterprise-attack-19.1"
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Server-Trace-ID"] = server_trace_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        # Only matched route templates and generated IDs are logged. Supplied
        # paths, query strings, request IDs, alert IDs and exceptions are data.
        route = request.scope.get("route")
        logging.getLogger("security_alert.api").info(json.dumps({
            "event": "request", "method": request.method,
            "route": getattr(route, "path", "unmatched"),
            "status": response.status_code,
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
            "request_id": server_trace_id,
        }))
        return response

    application.add_middleware(CORSMiddleware, allow_origins=origins,
        allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Request-ID", "X-API-Key"],
        expose_headers=["X-Request-ID", "X-Server-Trace-ID", "X-MITRE-ATTaCK-Version", "Retry-After"])
    application.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
    application.include_router(evaluate_router, tags=["evaluation"])
    application.include_router(rag_router, prefix="/rag", tags=["rag"])
    application.include_router(taxonomy_router, prefix="/taxonomy", tags=["taxonomy"])

    @application.get("/")
    async def health():
        return {"status": "ok", "stix_version": "19.1"}

    @application.get("/ready")
    async def readiness(request: Request):
        retriever = runtime.get_retriever(request)
        return {"status": "ready", "stix_version": "19.1",
                "subset_status": retriever.snapshot["subset_status"]}

    @application.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    async def analyst_ui():
        return HTMLResponse((PROJECT_ROOT / "ui/index.html").read_text(encoding="utf-8"))

    return application


app = create_app()
