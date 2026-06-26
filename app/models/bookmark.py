from pydantic import BaseModel

from app.models.ai import AIBookmarkClassification


class Bookmark(BaseModel):
    title: str
    url: str
    folder_path: str = ""
    added_at: str | None = None
    browser_source: str = "html_export"


class BookmarkAnalysis(BaseModel):
    title: str
    url: str
    normalized_url: str
    folder_path: str
    status: str
    category: str
    score: int
    recommended_action: str
    duplicate: bool = False
    reason: str = ""
    # Score que manda el orden/acción. = score local, salvo que el blending con IA lo modifique.
    effective_score: int = 0
    # Capa IA opcional (aditiva). None = no se enriqueció con IA.
    ai: AIBookmarkClassification | None = None
