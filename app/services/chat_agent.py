from __future__ import annotations

import json
import logging
from collections import Counter

from app.config import settings
from app.repositories.sqlite_repository import SQLiteRepository
from app.services.ai_classifier import is_ai_available

logger = logging.getLogger("app.chat")

SYSTEM = """Sos un asistente que ayuda al usuario a explorar sus marcadores YA analizados.
Tenés herramientas para CONSULTAR el conjunto. Es SOLO LECTURA: todavía no podés borrar,
mover ni modificar nada (si te lo piden, aclaralo y ofrecé consultarlo en su lugar).
Respondé en español, breve y concreto. No inventes: si una consulta no devuelve datos, decilo.
Cuando listes marcadores, mostrá el título y, si ayuda, la categoría o la acción recomendada.

CÓMO DEDUCIR EL TEMA ("¿de qué tratan?"):
- Las CATEGORÍAS son una taxonomía fija y genérica (python, gaming, entretenimiento, desconocido…).
  NO son el tema real. "desconocido" solo significa que las reglas no matchearon una keyword,
  NO que el tema sea un misterio. Nunca respondas que los marcadores "tratan de temas desconocidos".
- Para deducir el tema REAL mirá los TÍTULOS y los NOMBRES DE CARPETA: usá 'muestra_titulos' y
  'por_carpeta' de la herramienta estadisticas, y 'title'/'carpeta' de las búsquedas. Ahí suele
  estar el tema concreto (ej: una carpeta "Pkr / NUEVOS TUTOS POKER" indica que son sobre póker).
- Todavía NO leés el contenido de las páginas; te basás en título, URL y carpeta. Si te falta
  información para afirmar algo, decilo en vez de inventar."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_marcadores",
            "description": "Busca en los marcadores analizados. Todos los filtros son opcionales y se combinan (AND).",
            "parameters": {
                "type": "object",
                "properties": {
                    "termino": {"type": "string", "description": "Texto a buscar en título/URL/carpeta"},
                    "categoria": {"type": "string", "description": "Categoría exacta (ej: python, aws, gaming)"},
                    "accion": {"type": "string", "description": "Acción: ver_esta_semana, ver_luego, archivar, revisar_o_borrar, borrar_probable"},
                    "estado": {"type": "string", "description": "Estado del link: OK, BROKEN, REDIRECTED, FORBIDDEN, NOT_VALIDATED"},
                    "limite": {"type": "integer", "description": "Máximo de resultados (default 30)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estadisticas",
            "description": "Totales y conteos por categoría y por acción del conjunto analizado.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _rows() -> list[dict]:
    return SQLiteRepository().list_bookmarks()


def _categoria_efectiva(r: dict) -> str:
    """Categoría que ve el usuario: la de la IA si enriqueció esa fila, si no la de reglas."""
    return (r.get("ai_category") or r.get("category") or "desconocido")


def _score_efectivo(r: dict):
    """Score que manda (blended con IA); cae al local si la fila es previa a la IA."""
    return r.get("effective_score") if r.get("effective_score") is not None else r.get("score")


def buscar_marcadores(termino=None, categoria=None, accion=None, estado=None, limite=30) -> dict:
    term = (termino or "").lower()
    out = []
    for r in _rows():
        haystack = f"{r.get('title', '')} {r.get('url', '')} {r.get('folder_path', '')}".lower()
        if term and term not in haystack:
            continue
        # Se filtra por la categoría efectiva (IA cuando existe) para que coincida
        # con lo que el usuario ve; se acepta también la de reglas por retrocompat.
        if categoria and categoria.lower() not in {
            _categoria_efectiva(r).lower(), (r.get("category") or "").lower()
        }:
            continue
        if accion and (r.get("recommended_action") or "").lower() != accion.lower():
            continue
        if estado and (r.get("status") or "").upper() != estado.upper():
            continue
        out.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "categoria": _categoria_efectiva(r),
            "accion": r.get("recommended_action"),
            "score": _score_efectivo(r),
            "estado": r.get("status"),
            "carpeta": r.get("folder_path"),
            "motivo_ia": r.get("ai_reason"),
        })
    return {"total_encontrados": len(out), "resultados": out[: (limite or 30)]}


def estadisticas() -> dict:
    rows = _rows()
    # 'por_carpeta' y 'muestra_titulos' le dan al modelo la señal del TEMA real
    # (los nombres de carpeta y los títulos), que la taxonomía de categorías no aporta.
    titulos = [r.get("title") for r in rows if r.get("title")]
    return {
        "total": len(rows),
        "por_categoria": dict(Counter(_categoria_efectiva(r) for r in rows).most_common()),
        "por_carpeta": dict(Counter(r.get("folder_path") or "(sin carpeta)" for r in rows).most_common(15)),
        "por_accion": dict(Counter(r.get("recommended_action") for r in rows).most_common()),
        "muestra_titulos": titulos[:20],
    }


_DISPATCH = {
    "buscar_marcadores": buscar_marcadores,
    "estadisticas": lambda **_: estadisticas(),
}


def is_available() -> bool:
    return is_ai_available()


def answer(messages: list[dict], max_iters: int = 4) -> str:
    """Responde la última consulta del usuario usando tool-calling (solo lectura)."""
    if not is_available():
        return "La IA no está disponible (falta OPENAI_API_KEY). El chat necesita IA."

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_timeout_seconds)
        convo = [{"role": "system", "content": SYSTEM}, *messages]

        for _ in range(max_iters):
            resp = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                messages=convo,
                tools=TOOLS,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                reply = msg.content or "(sin respuesta)"
                logger.info("chat respuesta directa (sin tools): %r", reply[:160])
                return reply

            convo.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                fn = _DISPATCH.get(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                    result = fn(**args) if fn else {"error": "herramienta desconocida"}
                except Exception as exc:  # noqa: BLE001
                    result = {"error": str(exc)}
                resumen = result.get("total_encontrados", result.get("total", "?")) if isinstance(result, dict) else "?"
                logger.info("chat tool: %s(%s) -> total=%s", tc.function.name, args, resumen)
                convo.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False)})

        logger.warning("chat: se agotaron las %d iteraciones de tools", max_iters)
        return "No pude completar la consulta (demasiados pasos)."
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chat error: %s", exc)
        return "Hubo un error procesando la consulta."
