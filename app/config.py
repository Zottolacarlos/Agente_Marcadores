from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    reports_dir: Path = data_dir / "reports"
    input_dir: Path = data_dir / "input"
    database_path: Path = data_dir / "bookmarks.db"
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "8"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    # Tope de seguridad de cuántos bookmarks enriquece la IA (la IA clasifica TODOS
    # los analizados hasta este límite; el control real es --limit del análisis).
    ai_max_bookmarks: int = int(os.getenv("AI_MAX_BOOKMARKS", "200"))
    # Cuántos bookmarks van por llamada a la IA (batch): más barato y rápido que 1x1.
    ai_batch_size: int = int(os.getenv("AI_BATCH_SIZE", "20"))
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    ai_min_confidence: float = float(os.getenv("AI_MIN_CONFIDENCE", "0.7"))
    # Peso de la prioridad IA en el score efectivo (blending). 0 = solo local, 1 = solo IA.
    ai_blend_weight: float = float(os.getenv("AI_BLEND_WEIGHT", "0.6"))
    perfil_path: Path = base_dir / os.getenv("PERFIL_PATH", "perfil.md")


settings = Settings()
settings.reports_dir.mkdir(parents=True, exist_ok=True)
settings.input_dir.mkdir(parents=True, exist_ok=True)
