import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.api.routes import rag
from src.schemas import TechniqueCandidate

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as test_client:
        yield test_client


class FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(self, narrative, tactic=None, top_k=5):
        self.calls.append((narrative, tactic, top_k))
        candidates = [
            TechniqueCandidate(
                technique_id="T1059.001",
                technique_name="PowerShell",
                tactic="execution",
                description_excerpt="PowerShell execution",
                stix_version="19.1",
            )
        ]
        return candidates[:top_k]


async def test_rag_search_uses_validated_parameters(client, monkeypatch):
    retriever = FakeRetriever()
    monkeypatch.setattr(rag, "RETRIEVER", retriever)

    response = await client.post(
        "/rag/search",
        json={
            "narrative": "encoded PowerShell execution",
            "tactic": ["execution", "execution"],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["candidates"][0]["technique_id"] == "T1059.001"
    assert retriever.calls == [
        ("encoded PowerShell execution", ["execution"], 3)
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"narrative": ""},
        {"narrative": "alert", "top_k": 0},
        {"narrative": "alert", "top_k": 26},
        {"narrative": "alert", "top_k": "five"},
        {"narrative": "alert", "top_k": True},
        {"narrative": "alert", "tactic": ["defense-evasion"]},
    ],
)
async def test_rag_search_rejects_invalid_input(client, payload):
    response = await client.post("/rag/search", json=payload)
    assert response.status_code == 422


async def test_rag_search_treats_empty_tactic_as_all_scope(client, monkeypatch):
    retriever = FakeRetriever()
    monkeypatch.setattr(rag, "RETRIEVER", retriever)

    response = await client.post(
        "/rag/search",
        json={"narrative": "PowerShell", "tactic": [], "top_k": 1},
    )

    assert response.status_code == 200
    assert retriever.calls == [("PowerShell", None, 1)]
