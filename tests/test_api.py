import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Verdict" in data["name"]


@pytest.mark.asyncio
async def test_create_and_list_suites(client):
    suite_data = {
        "name": "Test Suite",
        "description": "testing",
        "judges": [
            {
                "name": "j1",
                "dimension": "accuracy",
                "rubric": "Score 1-5",
                "weight": 1.0,
                "scoring_scale": 5,
            }
        ],
        "aggregation": {"method": "weighted_average"},
    }
    resp = await client.post("/api/suites", json=suite_data)
    assert resp.status_code == 200
    created = resp.json()
    assert created["name"] == "Test Suite"
    assert "id" in created

    resp = await client.get("/api/suites")
    assert resp.status_code == 200
    suites = resp.json()
    assert len(suites) >= 1


@pytest.mark.asyncio
async def test_create_and_list_datasets(client):
    dataset_data = {
        "name": "Test Dataset",
        "entries": [
            {"input": "hello", "output": "world"},
            {"input": "foo", "output": "bar"},
        ],
    }
    resp = await client.post("/api/datasets", json=dataset_data)
    assert resp.status_code == 200
    created = resp.json()
    assert created["name"] == "Test Dataset"
    assert created["entry_count"] == 2

    resp = await client.get("/api/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) >= 1


@pytest.mark.asyncio
async def test_get_nonexistent_suite_404(client):
    resp = await client.get("/api/suites/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_run_404(client):
    resp = await client.get("/api/evaluations/nonexistent-id")
    assert resp.status_code == 404
