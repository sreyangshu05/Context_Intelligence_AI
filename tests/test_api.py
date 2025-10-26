import pytest
from fastapi.testclient import TestClient
from app.main import app
import io


client = TestClient(app)


def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "documents_ingested" in data
    assert "extractions_performed" in data
    assert "queries_answered" in data
    assert "audits_run" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_ingest_no_files():
    response = client.post("/ingest", files=[])
    assert response.status_code == 422


def test_extract_invalid_document():
    response = client.post("/extract", json={"document_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404


def test_ask_empty_question():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 400


def test_ask_valid_question():
    response = client.post("/ask", json={"question": "What is the effective date?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


def test_audit_invalid_document():
    response = client.post("/audit", json={"document_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404


def test_openapi_docs():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
