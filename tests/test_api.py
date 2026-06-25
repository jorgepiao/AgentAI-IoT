import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_ok(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_includes_mode(self, client):
        resp = client.get("/health")
        assert "mode" in resp.json()

    def test_health_includes_skills(self, client):
        resp = client.get("/health")
        skills = resp.json()["skills"]
        assert "iluminacion" in skills
        assert "clima" in skills

    def test_health_includes_llm_model(self, client):
        resp = client.get("/health")
        assert "llm_model" in resp.json()


class TestSkills:
    def test_list_skills_returns_200(self, client):
        resp = client.get("/skills")
        assert resp.status_code == 200

    def test_list_skills_contains_climate(self, client):
        resp = client.get("/skills")
        data = resp.json()
        assert "clima" in data
        assert data["clima"]["description"] != ""

    def test_list_skills_contains_lighting(self, client):
        resp = client.get("/skills")
        data = resp.json()
        assert "iluminacion" in data
        assert data["iluminacion"]["description"] != ""

    def test_list_skills_includes_tools(self, client):
        resp = client.get("/skills")
        data = resp.json()
        tools = data["iluminacion"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "set_light_state" in tool_names

    def test_climate_tools_three(self, client):
        resp = client.get("/skills")
        data = resp.json()
        assert len(data["clima"]["tools"]) == 3

    def test_lighting_tools_two(self, client):
        resp = client.get("/skills")
        data = resp.json()
        assert len(data["iluminacion"]["tools"]) == 2


class TestChat:
    def test_chat_no_skill_returns_error(self, client):
        resp = client.post("/chat", json={"message": "reproduce música"})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert "No se reconoció" in data["error"]

    def test_chat_no_llm_returns_503(self, client):
        resp = client.post("/chat", json={"message": "enciende las luces"})
        assert resp.status_code == 503
        data = resp.json()
        assert "LLM no configurado" in data["detail"]["error"]

    def test_chat_invalid_body(self, client):
        resp = client.post("/chat", json={})
        assert resp.status_code == 422


class TestState:
    def test_get_state_without_mqtt(self, client):
        resp = client.get("/state/sala/temperatura")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] is None
        assert "MQTT no conectado" in data["note"]

    def test_get_state_nested_topic(self, client):
        resp = client.get("/state/oficina/sensor/temperatura")
        assert resp.status_code == 200


class TestCORS:
    def test_cors_headers_present(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp.headers
