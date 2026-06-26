from pydantic import BaseModel
from .bookmark import BookmarkAnalysis


class AnalysisSummary(BaseModel):
    total: int
    ok: int
    broken: int
    duplicates: int
    review_or_delete: int
    top_recommended: list[BookmarkAnalysis]
    reports: list[str]
    warning: str | None = None
    ai_used: bool = False
    ai_enriched: int = 0
    ai_low_confidence: int = 0
