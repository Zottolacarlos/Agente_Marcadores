from __future__ import annotations


from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings
from app.models.bookmark import Bookmark
from app.repositories.sqlite_repository import SQLiteRepository
from app.services.analyzer import run_analysis
from app.services.chromium_bookmark_reader import read_chromium_bookmarks
from app.services.html_bookmark_parser import parse_bookmarks_html

router = APIRouter(prefix="/api", tags=["api"])


class AnalyzeRequest(BaseModel):
    file_path: str | None = None
    browser: str | None = None
    folder: str = "Pendientes"
    limit: int | None = Field(default=None, ge=1)
    skip_validation: bool = False


@router.post("/analyze")
def api_analyze(payload: AnalyzeRequest):
    bookmarks: list[Bookmark] = []

    if payload.file_path:
        with open(payload.file_path, "rb") as f:
            bookmarks.extend(parse_bookmarks_html(f.read()))

    if payload.browser:
        browser_bookmarks, error = read_chromium_bookmarks(payload.browser)
        if error:
            return {"error": error}
        bookmarks.extend(browser_bookmarks)

    return run_analysis(
        bookmarks,
        payload.folder,
        limit=payload.limit,
        skip_validation=payload.skip_validation,
    ).model_dump()


@router.get("/reports")
def api_reports():
    return {"reports": [p.name for p in settings.reports_dir.glob("*") if p.is_file()]}


@router.get("/bookmarks")
def api_bookmarks():
    return SQLiteRepository().list_bookmarks()
