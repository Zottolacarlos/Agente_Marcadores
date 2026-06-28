from __future__ import annotations

import re

KEY_CATEGORIES = {"trabajo", "ia", "python", "aws", "backend", "devops", "database", "git", "jobs"}
LEISURE_CATEGORIES = {"gaming", "comics", "entretenimiento", "deportes"}

# Patrones con límite de palabra (\b…\b) para evitar falsos positivos por substring,
# ej: "dev" NO debe matchear dentro de "Devastator". Los stems largos seguros usan \w*
# (arquitect\w* → arquitectura/arquitecto), los cortos van como palabra entera (dev, api).
_DEV_PAT = re.compile(
    r"\b(?:backend|back-end|api|rest|server|service|dev|developer|"
    r"arquitect\w*|architectur\w*|microservic\w*|desarroll\w*)\b",
    re.IGNORECASE,
)
_LEARN_PAT = re.compile(r"\b(?:curso|cursos|tutorial|tutoriales|guide|gu[ií]a|learn|aprend\w*)\b", re.IGNORECASE)
_NEWS_PAT = re.compile(r"\b(?:news|noticia|noticias|breaking)\b", re.IGNORECASE)
_OLD_YEAR_PAT = re.compile(r"\b(?:2018|2019|2020|2021)\b")


def action_from_score(score: int, status: str, duplicate: bool) -> str:
    """Mapea un score (0-100) a la acción recomendada. Usado por el scoring local
    y por el blending para mantener un único contrato score→acción."""
    if status == "BROKEN" or duplicate:
        return "revisar_o_borrar"
    if score >= 70:
        return "ver_esta_semana"
    if score >= 45:
        return "ver_luego"
    if score >= 25:
        return "archivar"
    return "borrar_probable"


def score_bookmark(category: str, status: str, folder: str, duplicate: bool, title: str, url: str) -> tuple[int, str, str]:
    score = 30
    # Cada factor se anota con su aporte en puntos para que el front pueda
    # explicar de dónde sale el número final (ej: "base 30, +30 categoría clave…").
    reason: list[str] = ["base 30"]
    text = f"{title} {url} {folder}".lower()

    def add(delta: int, label: str) -> None:
        nonlocal score
        score += delta
        sign = f"+{delta}" if delta >= 0 else str(delta)
        reason.append(f"{label} ({sign})")

    if category in KEY_CATEGORIES:
        add(30, "categoría clave")
    elif category in {"finanzas", "english"}:
        add(20, "categoría útil")
    elif category in LEISURE_CATEGORIES:
        add(10, "ocio/interés personal")

    if _DEV_PAT.search(text):
        add(20, "relevante a desarrollo/backend")

    if _LEARN_PAT.search(text):
        add(10, "contenido de aprendizaje")

    if "pendientes" in folder.lower():
        add(15, "estaba en Pendientes")

    if status == "OK":
        add(10, "link activo")
    elif status == "NOT_VALIDATED":
        reason.append("validación omitida (0)")
    elif status == "BROKEN":
        add(-30, "link roto")
    elif status in {"TIMEOUT", "UNKNOWN"}:
        add(-10, "estado incierto")
    elif status in {"FORBIDDEN", "REDIRECTED"}:
        reason.append(f"estado {status.lower()} (0)")

    if duplicate:
        add(-15, "duplicado")

    if _NEWS_PAT.search(text):
        add(-10, "posible contenido temporal")
    if _OLD_YEAR_PAT.search(text):
        add(-10, "posible contenido viejo")

    score = max(0, min(100, score))
    action = action_from_score(score, status, duplicate)

    return score, action, ", ".join(reason)
