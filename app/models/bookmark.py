from pydantic import BaseModel


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
