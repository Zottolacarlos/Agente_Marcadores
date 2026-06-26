from __future__ import annotations

import re
from urllib.parse import urlparse

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
    "comics": ["comic", "comics", "batman", "manga", "anime", "dc", "marvel", "ovni", "ecc", "transformers"],
    "deportes": ["futbol", "fútbol", "nba", "tenis", "deporte", "deportes", "ajedrez", "chess"],
    "noticias": ["news", "noticia", "noticias", "breaking", "diario", "journal", "review"],
    "entretenimiento": ["youtube", "netflix", "movie", "pelicula", "película", "serie", "streaming", "memes", "retro"],
    "familia": ["familia", "kids", "viaje familiar", "family"],
}

# Mapa de dominios → categoría. Se usa como respaldo cuando el título/carpeta no
# alcanza para clasificar. El host es una señal mucho más confiable que un
# substring perdido en el path o el query de la URL.
DOMAIN_RULES: list[tuple[str, str]] = [
    ("youtube.com", "entretenimiento"),
    ("youtu.be", "entretenimiento"),
    ("netflix.com", "entretenimiento"),
    ("twitch.tv", "entretenimiento"),
    ("vimeo.com", "entretenimiento"),
    ("spotify.com", "entretenimiento"),
    ("docs.aws.amazon.com", "aws"),
    ("aws.amazon.com", "aws"),
    ("github.com", "git"),
    ("gitlab.com", "git"),
    ("stackoverflow.com", "backend"),
    ("pypi.org", "python"),
    ("readthedocs.io", "python"),
    ("linkedin.com", "jobs"),
    ("indeed.com", "jobs"),
    ("binance.com", "finanzas"),
    ("dolarhoy.com", "finanzas"),
    ("mercadolibre.com", "compras"),
    ("steampowered.com", "gaming"),
    ("steamcommunity.com", "gaming"),
    ("steamdb.info", "gaming"),
]


def _compile(keywords: list[str]) -> re.Pattern[str]:
    # \b…\b exige límite de palabra: "rag" ya no matchea dentro de "storage",
    # ni "s3" dentro de un ID de YouTube. re.escape protege keywords con / o -.
    alternation = "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True))
    return re.compile(rf"\b(?:{alternation})\b", re.IGNORECASE)


_COMPILED: dict[str, re.Pattern[str]] = {cat: _compile(kws) for cat, kws in RULES.items()}


def _host(url: str) -> str:
    try:
        host = urlparse(url if "://" in url else f"//{url}", scheme="http").netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def classify(title: str, url: str, folder: str) -> str:
    # El contenido se matchea contra título + carpeta (señales de intención),
    # NO contra la URL cruda, que es la fuente principal de falsos positivos.
    content = f"{title} {folder}"
    for category, pattern in _COMPILED.items():
        if pattern.search(content):
            return category

    # Respaldo por dominio cuando el título/carpeta no dicen nada útil.
    host = _host(url)
    if host:
        for domain, category in DOMAIN_RULES:
            if host == domain or host.endswith(f".{domain}"):
                return category

    return "desconocido"
