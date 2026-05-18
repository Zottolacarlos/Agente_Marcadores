from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.models.bookmark import Bookmark
from app.services.analyzer import run_analysis
from app.services.chromium_bookmark_reader import read_chromium_bookmarks
from app.services.html_bookmark_parser import parse_bookmarks_html

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.base_dir / "app" / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, target_folder: str = Form("Pendientes"), use_file: bool = Form(False), use_chrome: bool = Form(False), use_edge: bool = Form(False), file: UploadFile | None = None):
    bookmarks: list[Bookmark] = []
    if use_file and file:
        content = await file.read()
        bookmarks.extend(parse_bookmarks_html(content))
    if use_chrome:
        bms, _ = read_chromium_bookmarks("chrome")
        bookmarks.extend(bms)
    if use_edge:
        bms, _ = read_chromium_bookmarks("edge")
        bookmarks.extend(bms)
    summary = run_analysis(bookmarks, target_folder)
    return templates.TemplateResponse("summary.html", {"request": request, "summary": summary})


@router.get("/reports/{report_name}")
def get_report(report_name: str):
    file_path = settings.reports_dir / report_name
    return FileResponse(file_path)
