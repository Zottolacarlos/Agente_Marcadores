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

# Fila enriquecida por IA: la categoría de reglas es "desconocido" pero la IA la
# reclasificó y hubo blending (effective_score != score). El chat debe mostrar lo de la IA.
_ROWS_IA = [
    {"title": "Tuto de push/fold", "url": "https://ej.com/pkr1", "folder_path": "Pkr/NUEVOS TUTOS POKER",
     "category": "desconocido", "recommended_action": "ver_luego", "score": 40, "status": "OK",
     "effective_score": 72, "ai_category": "poker", "ai_reason": "Tutorial de estrategia de póker."},
    {"title": "Rangos preflop", "url": "https://ej.com/pkr2", "folder_path": "Pkr",
     "category": "desconocido", "recommended_action": "archivar", "score": 35, "status": "OK",
     "effective_score": 30, "ai_category": "poker", "ai_reason": "Tabla de rangos."},
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
    # Ahora también expone carpetas y una muestra de títulos (señal del tema real).
    assert st["por_carpeta"]["Pendientes"] == 2
    assert "FastAPI docs" in st["muestra_titulos"]


def test_estadisticas_usa_categoria_ia(monkeypatch):
    monkeypatch.setattr(chat_agent, "_rows", lambda: _ROWS_IA)
    st = chat_agent.estadisticas()
    # La categoría efectiva (IA) reemplaza a "desconocido" de reglas.
    assert st["por_categoria"].get("poker") == 2
    assert "desconocido" not in st["por_categoria"]
    # La carpeta delata el tema real aunque las reglas dijeran "desconocido".
    assert "Pkr/NUEVOS TUTOS POKER" in st["por_carpeta"]


def test_buscar_usa_categoria_y_score_efectivos(monkeypatch):
    monkeypatch.setattr(chat_agent, "_rows", lambda: _ROWS_IA)
    res = chat_agent.buscar_marcadores(categoria="poker")
    assert res["total_encontrados"] == 2
    primero = res["resultados"][0]
    assert primero["categoria"] == "poker"
    # Muestra el score efectivo (blended), no el local.
    assert primero["score"] == 72
    assert primero["motivo_ia"] == "Tutorial de estrategia de póker."


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
