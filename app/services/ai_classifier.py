from app.config import settings


class AIClassifier:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key)

    def enrich_category(self, title: str, url: str, category: str) -> str | None:
        if not self.enabled:
            return None
        return None
