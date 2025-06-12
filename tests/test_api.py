from fastapi.testclient import TestClient
import importlib

api_mod = importlib.import_module("app.main")
client = TestClient(api_mod.api)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("tor") in ("ok", "fail")
