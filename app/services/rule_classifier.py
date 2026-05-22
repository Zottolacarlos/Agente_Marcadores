from __future__ import annotations

RULES: dict[str, list[str]] = {
    "ia": [
        "openai", "chatgpt", "claude", "anthropic", "gemini", "llm", "rag", "langchain", "langgraph",
        "agent", "agente", "agents", "genai", "genia", "inteligencia artificial", "machine learning",
        "deep learning", "embedding", "vector", "milvus", "zilliz", "ollama", "prompt",
    ],
    "python": [
        "python", "fastapi", "django", "flask", "pandas", "pytest", "pydantic", "sqlalchemy", "poetry",
        "uvicorn", "asyncio", "jupyter", "notebook",
    ],
    "aws": [
        "aws", "amazon web services", "cloudformation", "bedrock", "lambda", "s3", "dynamodb", "cloudwatch",
        "eventbridge", "sqs", "sns", "cdk", "ecs", "eks", "api gateway",
    ],
    "backend": [
        "backend", "back-end", "api", "rest", "microservice", "microservicio", "architecture", "arquitectura",
        "server", "service", "clean architecture", "hexagonal",
    ],
    "frontend": ["frontend", "front-end", "javascript", "typescript", "react", "vue", "angular", "html", "css", "tailwind"],
    "devops": ["docker", "kubernetes", "k8s", "jenkins", "gitlab ci", "github actions", "ci/cd", "cicd", "terraform", "ansible", "devops"],
    "database": ["sql", "postgres", "postgresql", "mysql", "mongodb", "sqlite", "redis", "database", "base de datos"],
    "git": ["git", "github", "gitlab", "merge", "pull request", "branch", "commit"],
    "english": ["english", "inglés", "ingles", "pronunciation", "grammar", "listening", "speaking"],
    "jobs": ["linkedin", "indeed", "job", "jobs", "trabajo", "cv", "resume", "recruiter", "recruiting", "entrevista", "interview"],
    "finanzas": [
        "binance", "payoneer", "skrill", "neteller", "dolar", "dólar", "dolarhoy", "invertironline",
        "iol", "airtm", "astropay", "fiwind", "crypto", "bitcoin", "usdt", "wallet", "exchange", "finance",
    ],
    "gaming": ["steam", "epic", "xbox", "game pass", "gog", "fitgirl", "gaming", "juego", "games", "mod", "mods", "nintendo", "playstation"],
    "compras": ["mercadolibre", "amazon", "shop", "tienda", "comprar", "shopping", "wishlist", "lista deseados"],
    "comics": ["comic", "comics", "batman", "manga", "anime", "dc", "marvel", "ovni", "ecc"],
    "deportes": ["futbol", "fútbol", "nba", "tenis", "deporte", "deportes", "ajedrez", "chess"],
    "noticias": ["news", "noticia", "noticias", "breaking", "diario", "journal", "review"],
    "entretenimiento": ["youtube", "netflix", "movie", "pelicula", "película", "serie", "streaming", "memes", "retro"],
    "familia": ["familia", "kids", "viaje familiar", "family"],
}


def classify(title: str, url: str, folder: str) -> str:
    text = f"{title} {url} {folder}".lower()
    for category, keywords in RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "desconocido"
