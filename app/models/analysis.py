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
