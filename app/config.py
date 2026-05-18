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


settings = Settings()
settings.reports_dir.mkdir(parents=True, exist_ok=True)
settings.input_dir.mkdir(parents=True, exist_ok=True)
