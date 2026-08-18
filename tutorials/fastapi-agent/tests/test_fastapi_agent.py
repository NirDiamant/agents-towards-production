"""
Unit tests for the FastAPI Agent application
"""
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from scripts directory
from scripts.fastapi_agent import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_agent_endpoint():
    """Test the synchronous agent endpoint"""
    response = client.post(
        "/agent",
        json={"query": "Test query"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
    assert "Agent" in response.json()["response"]

def test_stream_endpoint():
    """Test the streaming agent endpoint"""
    with client.stream("POST", "/agent/stream", json={"query": "Test query"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        content = "".join(response.iter_text())
        assert 'data: {"token":' in content
