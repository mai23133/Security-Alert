"""One verified KB generation and bounded worker capacity per application."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
from pathlib import Path

from fastapi import HTTPException, Request

from src.rag.ingest_stix import STIX_PATH, PINNED_STIX_SHA256, external_id, in_scope, load_stix_objects, metadata_for, to_candidate
from src.rag.retriever import BaselineRetriever

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data/processed/kb_snapshot.json"


def load_knowledge_base(snapshot_path: Path) -> BaselineRetriever:
    retriever = BaselineRetriever(snapshot_path, snapshot_path, snapshot_path=snapshot_path)
    snapshot = retriever.snapshot
    if (snapshot["stix_version"] != "enterprise-attack-19.1"
        or snapshot["stix_sha256"] != hashlib.sha256(STIX_PATH.read_bytes()).hexdigest()
        or snapshot["stix_sha256"] != PINNED_STIX_SHA256
        or {c.technique_id for c in retriever.candidates} != retriever.allowlist_ids
        or not retriever.candidates):
        raise ValueError("Invalid pinned KB snapshot")
    source = {external_id(o): o for o in load_stix_objects(STIX_PATH) if in_scope(o)}
    for candidate in retriever.candidates:
        obj = source.get(candidate.technique_id)
        if obj is None or candidate != to_candidate(obj) or retriever.metadata.get(candidate.technique_id) != metadata_for(obj):
            raise ValueError("Snapshot differs from pinned STIX")
    return retriever


async def get_retriever(request: Request) -> BaselineRetriever:
    """Return the loaded snapshot without dispatching a trivial dependency to a worker."""
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None:
        raise HTTPException(503, detail={"code": "KNOWLEDGE_BASE_UNAVAILABLE", "message": "Pinned ATT&CK knowledge base is unavailable."})
    return retriever


async def run_bounded(request: Request, function, *args):
    """A timed-out worker holds its slot until it actually finishes.

    Cancelling an HTTP request cannot kill Python threads. Shielding the work
    and releasing capacity on completion bounds residual work and its queue.
    """
    slots = request.app.state.worker_slots
    remaining = lambda: max(0.001, request.state.deadline - time.monotonic() - 0.01)
    try:
        await asyncio.wait_for(slots.acquire(), timeout=remaining())
    except TimeoutError:
        raise HTTPException(504, detail={"code": "INFERENCE_TIMEOUT", "message": "Inference timed out. Human review is required."}) from None
    loop = asyncio.get_running_loop()
    try:
        future = request.app.state.executor.submit(function, *args)
    except BaseException:
        slots.release()
        raise

    def release_slot(done):
        slots.release()
        if not done.cancelled():
            done.exception()

    future.add_done_callback(lambda done: loop.call_soon_threadsafe(release_slot, done))
    while not future.done():
        if time.monotonic() >= request.state.deadline - 0.01:
            raise HTTPException(504, detail={"code": "INFERENCE_TIMEOUT", "message": "Inference timed out. Human review is required."}) from None
        await asyncio.sleep(min(0.01, remaining()))
    return future.result()
