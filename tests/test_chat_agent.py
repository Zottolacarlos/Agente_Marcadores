from fastapi.testclient import TestClient

from app.main import app
from app.services import chat_agent

client = TestClient(app)

_ROWS = [
    {"title": "FastAPI docs", "url": "https://fastapi.tiangolo.com", "folder_path": "Pendientes",
     "category": "python", "recommended_action": "ver_esta_semana", "score": 90, "status": "OK"},
    {"title": "Un video", "url": "https://youtube.com/x", "folder_path": "Games",
     "category": "entretenimiento", "recommended_action": "archivar", "score": 30, "status": "OK"},
    {"title": "Link muerto", "url": "https://nope.invalid", "folder_path": "Pendientes",
     "category": "desconocido", "recommended_action": "revisar_o_borrar", "score": 10, "status": "BROKEN"},
]


def test_buscar_por_categoria(monkeypatch):
    monkeypatch.setattr(chat_agent, "_rows", lambda: _ROWS)
    res = chat_agent.buscar_marcadores(categoria="python")
    assert res["total_encontrados"] == 1
    assert res["resultados"][0]["title"] == "FastAPI docs"


def test_buscar_por_estado(monkeypatch):
    monkeypatch.setattr(chat_agent, "_rows", lambda: _ROWS)
    res = chat_agent.buscar_marcadores(estado="BROKEN")
    assert res["total_encontrados"] == 1


def test_estadisticas(monkeypatch):
    monkeypatch.setattr(chat_agent, "_rows", lambda: _ROWS)
    st = chat_agent.estadisticas()
    assert st["total"] == 3
    assert st["por_categoria"]["python"] == 1


def test_chat_unavailable(monkeypatch):
    monkeypatch.setattr(chat_agent, "is_available", lambda: False)
    reply = chat_agent.answer([{"role": "user", "content": "hola"}])
    assert "no está disponible" in reply.lower()


def test_chat_endpoint(monkeypatch):
    monkeypatch.setattr(chat_agent, "answer", lambda messages: "Tenés 1 link de python.")
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "¿qué tengo de python?"}]})
    assert r.status_code == 200
    assert r.json()["reply"] == "Tenés 1 link de python."


def test_chat_endpoint_empty():
    r = client.post("/chat", json={"messages": []})
    assert r.status_code == 200
    assert "Escribí" in r.json()["reply"]
