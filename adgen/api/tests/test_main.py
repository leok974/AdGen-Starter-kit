from fastapi.testclient import TestClient
from adgen.api.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_read_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
