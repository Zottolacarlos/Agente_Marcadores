from __future__ import annotations

import json
import re

from app.config import settings
from app.models.ai import AIBookmarkClassification

# Taxonomía de respaldo si no hay perfil.md o no se puede parsear su sección 7.
DEFAULT_TAXONOMY = [
    "ia", "python", "backend", "aws", "devops", "database", "frontend", "git",
    "jobs", "finanzas", "english", "gaming", "comics", "compras", "deportes",
    "noticias", "entretenimiento", "familia", "educacion", "referencia", "desconocido",
]

BASE_INSTRUCTIONS = """\
Sos un asistente que ayuda a un usuario a ordenar y priorizar sus bookmarks/favoritos.

Tu tarea: para UN bookmark, decidir categoría e importancia usando SOLO el título, la URL,
la carpeta y el PERFIL DEL USUARIO que se incluye más abajo.

Reglas anti-alucinación (importantes):
- No inventes nada sobre el contenido de la página: no la leíste.
- Si el título/URL/carpeta no alcanzan para decidir, usá category "desconocido" y confidence baja (< 0.5).
- La "reason" debe ser breve y basarse solo en lo que se ve y en el perfil.
- Respetá las "Reglas personales" del perfil cuando apliquen.
- La CARPETA es solo una pista DÉBIL, no decisiva: clasificá por lo que el link
  realmente es (título + URL). Ej: un tutorial de edición de video guardado en una
  carpeta "Games" NO es gaming.

Respondé SOLO JSON válido con este esquema:
{
  "category": "...",
  "subcategory": "...",
  "intent": "...",
  "priority": 0-100,
  "recommended_action": "leer_hoy|ver_esta_semana|ver_luego|archivar|borrar_probable|revisar_manual",
  "reason": "...",
  "confidence": 0.0-1.0
}\
"""


def load_profile() -> str | None:
    """Lee perfil.md si existe. Si no, devuelve None (la IA funciona genérica)."""
    try:
        text = settings.perfil_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def _parse_taxonomy(profile: str) -> list[str]:
    """Extrae la lista de categorías del bloque de código bajo la sección 'Taxonomía'."""
    match = re.search(r"Taxonom[ií]a.*?```[a-z]*\n(.*?)```", profile, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    lines = [ln.strip() for ln in match.group(1).splitlines()]
    return [ln for ln in lines if ln and " " not in ln]


def load_taxonomy() -> list[str]:
    profile = load_profile()
    if profile:
        parsed = _parse_taxonomy(profile)
        if parsed:
            return parsed
    return DEFAULT_TAXONOMY


def build_system_prompt() -> str:
    """Arma el prompt del sistema: instrucciones + taxonomía cerrada + perfil.

    El perfil es estático, así que va en el mensaje 'system' y OpenAI lo cachea
    automáticamente entre llamadas (prompt caching), abaratando el costo.
    """
    taxonomy = load_taxonomy()
    parts = [
        BASE_INSTRUCTIONS,
        "Categorías permitidas (elegí EXACTAMENTE una de esta lista):\n" + ", ".join(taxonomy),
    ]
    profile = load_profile()
    if profile:
        parts.append("PERFIL DEL USUARIO:\n" + profile)
    return "\n\n".join(parts)


def enforce_taxonomy(category: str, taxonomy: list[str]) -> str:
    """Backstop anti-alucinación: si la IA inventa una categoría fuera de la lista,
    se fuerza a 'desconocido'."""
    return category if category in taxonomy else "desconocido"


def is_ai_available() -> bool:
    """True solo si hay API key y el cliente está instalado. Nunca lanza."""
    if not settings.openai_api_key:
        return False
    try:
        import openai  # noqa: F401
    except ImportError:
        return False
    return True


def build_payload(
    *, title: str, url: str, folder_path: str, status: str, rule_category: str, rule_score: int
) -> dict:
    """Metadata mínima que se envía a la IA. NO incluye contenido de la página."""
    return {
        "title": title,
        "url": url,
        "folder_path": folder_path,
        "status": status,
        "rule_category": rule_category,
        "rule_score": rule_score,
    }


def classify_bookmark_with_ai(payload: dict) -> AIBookmarkClassification | None:
    """Devuelve la clasificación IA o None si IA no está disponible o algo falla.

    Cualquier error (sin key, timeout, rate limit, JSON inválido) se traga y
    devuelve None para que el análisis siga con el resultado local.
    """
    if not is_ai_available():
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_timeout_seconds)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content or ""
        result = AIBookmarkClassification(**json.loads(content))
        result.category = enforce_taxonomy(result.category, load_taxonomy())
        return result
    except Exception:
        return None


def classify_bookmarks_batch(payloads: list[dict]) -> list[AIBookmarkClassification | None]:
    """Clasifica MUCHOS bookmarks mandando varios por llamada (batch).

    Devuelve una lista alineada 1:1 con `payloads` (None donde la IA no opinó o falló).
    Cada item lleva un "id" para alinear la respuesta aunque la IA cambie el orden o
    devuelva de más/menos. Cualquier error en un lote deja esos items en None (fallback local).
    """
    results: list[AIBookmarkClassification | None] = [None] * len(payloads)
    if not is_ai_available() or not payloads:
        return results

    try:
        from openai import OpenAI
    except ImportError:
        return results

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_timeout_seconds)
    system = build_system_prompt()
    taxonomy = load_taxonomy()
    size = max(1, settings.ai_batch_size)

    for start in range(0, len(payloads), size):
        chunk = payloads[start : start + size]
        items = [{"id": start + i, **p} for i, p in enumerate(chunk)]
        user = (
            "Clasificá CADA bookmark de esta lista. Devolvé SOLO JSON válido con la forma "
            '{"results": [ ... ]}, un objeto por bookmark, cada uno con su "id" original '
            "y los campos del esquema.\n" + json.dumps(items, ensure_ascii=False)
        )
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            data = json.loads(response.choices[0].message.content or "")
            for obj in data.get("results", []):
                idx = obj.get("id")
                if not isinstance(idx, int) or not (0 <= idx < len(payloads)):
                    continue
                try:
                    cls = AIBookmarkClassification(**{k: v for k, v in obj.items() if k != "id"})
                    cls.category = enforce_taxonomy(cls.category, taxonomy)
                    results[idx] = cls
                except Exception:
                    continue
        except Exception:
            continue  # ese lote queda en None -> fallback local

    return results
