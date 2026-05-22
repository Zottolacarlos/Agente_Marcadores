from __future__ import annotations

KEY_CATEGORIES = {"trabajo", "ia", "python", "aws", "backend", "devops", "database", "git", "jobs"}
LEISURE_CATEGORIES = {"gaming", "comics", "entretenimiento", "deportes"}


def score_bookmark(category: str, status: str, folder: str, duplicate: bool, title: str, url: str) -> tuple[int, str, str]:
    score = 30
    reason: list[str] = []
    text = f"{title} {url} {folder}".lower()

    if category in KEY_CATEGORIES:
        score += 30
        reason.append("categoría clave")
    elif category in {"finanzas", "english"}:
        score += 20
        reason.append("categoría útil")
    elif category in LEISURE_CATEGORIES:
        score += 10
        reason.append("ocio/interés personal")

    if any(k in text for k in ["backend", "arquitect", "architecture", "api", "microservice", "microservicio", "dev"]):
        score += 20
        reason.append("relevante a desarrollo/backend")

    if any(k in text for k in ["curso", "tutorial", "guide", "guía", "learn", "aprender"]):
        score += 10
        reason.append("contenido de aprendizaje")

    if "pendientes" in folder.lower():
        score += 15
        reason.append("estaba en Pendientes")

    if status == "OK":
        score += 10
        reason.append("link activo")
    elif status == "NOT_VALIDATED":
        reason.append("validación omitida")
    elif status == "BROKEN":
        score -= 30
        reason.append("link roto")
    elif status in {"TIMEOUT", "UNKNOWN"}:
        score -= 10
        reason.append("estado incierto")
    elif status in {"FORBIDDEN", "REDIRECTED"}:
        reason.append(f"estado {status.lower()}")

    if duplicate:
        score -= 15
        reason.append("duplicado")

    if any(k in text for k in ["news", "noticia", "breaking"]):
        score -= 10
        reason.append("posible contenido temporal")
    if any(year in text for year in ["2018", "2019", "2020", "2021"]):
        score -= 10
        reason.append("posible contenido viejo")

    score = max(0, min(100, score))

    if status == "BROKEN" or duplicate:
        action = "revisar_o_borrar"
    elif score >= 70:
        action = "ver_esta_semana"
    elif score >= 45:
        action = "ver_luego"
    elif score >= 25:
        action = "archivar"
    else:
        action = "borrar_probable"

    return score, action, ", ".join(reason)
