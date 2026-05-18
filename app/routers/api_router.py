from fastapi import APIRouter
from pydantic import BaseModel
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


@router.post("/analyze")
def api_analyze(payload: AnalyzeRequest):
    bookmarks: list[Bookmark] = []
    if payload.file_path:
        with open(payload.file_path, "rb") as f:
            bookmarks.extend(parse_bookmarks_html(f.read()))
    if payload.browser:
        bms, err = read_chromium_bookmarks(payload.browser)
        if err:
            return {"error": err}
        bookmarks.extend(bms)
    return run_analysis(bookmarks, payload.folder).model_dump()


@router.get("/reports")
def api_reports():
    from pathlib import Path
    return {"reports": [p.name for p in Path('data/reports').glob('*') if p.is_file()]}


@router.get("/bookmarks")
def api_bookmarks():
    return SQLiteRepository().list_bookmarks()
