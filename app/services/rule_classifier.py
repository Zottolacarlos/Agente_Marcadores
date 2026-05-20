RULES = {
    "aws": ["aws", "amazon", "cloudformation", "bedrock"],
    "python": ["python", "fastapi", "django", "pandas"],
    "ia": ["langgraph", "openai", "llm", "rag", "agent"],
    "entretenimiento": ["youtube", "netflix", "movie", "comic", "batman"],
    "compras": ["mercadolibre", "amazon", "shop"],
    "deportes": ["futbol", "nba", "tenis", "deportes"],
    "noticias": ["news", "noticia", "breaking"],
    "tecnologia": ["tech", "tecnologia", "software"],
    "estudio": ["curso", "learn", "tutorial", "study"],
    "trabajo": ["jira", "confluence", "meeting", "work"],
    "familia": ["familia", "kids", "viaje familiar"],
}


def classify(title: str, url: str, folder: str) -> str:
    text = f"{title} {url} {folder}".lower()
    for category, keywords in RULES.items():
        if any(word in text for word in keywords):
            return category
    return "desconocido"
