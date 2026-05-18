def score_bookmark(category: str, status: str, folder: str, duplicate: bool, title: str, url: str) -> tuple[int, str, str]:
    score = 30
    reason = []
    if category in {"trabajo", "ia", "python", "aws"}:
        score += 30
        reason.append("categoría clave")
    if any(k in f"{title} {url}".lower() for k in ["backend", "arquitect", "api", "microservice", "dev"]):
        score += 20
        reason.append("relevante a backend")
    if "pendientes" in folder.lower():
        score += 15
        reason.append("estaba en Pendientes")
    if status == "OK":
        score += 10
    if status == "BROKEN":
        score -= 30
    if status in {"TIMEOUT", "UNKNOWN"}:
        score -= 10
    if duplicate:
        score -= 15
        reason.append("duplicado")
    if "news" in url.lower() or "2020" in title:
        score -= 20

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
