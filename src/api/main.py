"""
FastAPI application entry point.
Week 3 deliverable — loads .env, mounts routes, adds MITRE attribution header.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes.alerts import router as alerts_router
from src.api.routes.taxonomy import router as taxonomy_router

load_dotenv()

app = FastAPI(
    title="Security Alert → ATT&CK Inference API",
    description="Advisory tagging only. Not autonomous SOC action.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MITRE attribution header on every response (spec section 10)
@app.middleware("http")
async def add_mitre_header(request, call_next):
    response = await call_next(request)
    response.headers["X-MITRE-ATTaCK-Version"] = "enterprise-attack-19.1"
    return response

app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(taxonomy_router, prefix="/taxonomy", tags=["taxonomy"])

@app.get("/")
def health():
    return {"status": "ok", "stix_version": "19.1"}