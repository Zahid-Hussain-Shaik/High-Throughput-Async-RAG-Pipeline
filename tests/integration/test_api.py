"""Run with RUN_INTEGRATION=1 against PostgreSQL/pgvector and Redis."""
import os
import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="set RUN_INTEGRATION=1 with PostgreSQL/Redis available")

def test_document_to_query_round_trip():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        created = client.post("/api/v1/documents", json={
            "title": "Integration runbook",
            "content": "A priority one incident must be escalated to the on-call manager within fifteen minutes.",
            "metadata": {"test": True},
        })
        assert created.status_code == 201
        document_id = created.json()["id"]
        assert client.get(f"/api/v1/documents/{document_id}").status_code == 200
        answer = client.post("/api/v1/query", json={"query": "When must a priority one incident be escalated?"})
        assert answer.status_code == 200
        assert answer.json()["grounded"] is True
