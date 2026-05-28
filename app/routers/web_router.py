from __future__ import annotations

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


def _parse_limit(raw_limit: str | None) -> tuple[int | None, str | None]:
    if raw_limit is None or raw_limit.strip() == "":
        return None, None

    try:
        limit = int(raw_limit)
    except ValueError:
        return None, "El límite debe ser un número entero."

    if limit < 1:
        return None, "El límite debe ser mayor o igual a 1."

    return limit, None


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "defaults": {
                "target_folder": "Pendientes",
                "limit": "",
                "skip_validation": True,
            },
        },
    )


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    target_folder: str = Form("Pendientes"),
    limit: str = Form(""),
    skip_validation: bool = Form(False),
    use_file: bool = Form(False),
    use_chrome: bool = Form(False),
    use_edge: bool = Form(False),
    file: UploadFile | None = None,
):
    bookmarks: list[Bookmark] = []
    source_errors: list[str] = []
    selected_sources: list[str] = []

    parsed_limit, limit_error = _parse_limit(limit)
    if limit_error:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "request": request,
                "error": limit_error,
                "defaults": {
                    "target_folder": target_folder,
                    "limit": limit,
                    "skip_validation": skip_validation,
                },
            },
            status_code=400,
        )

    if use_file or (file and file.filename):
        if not file or not file.filename:
            source_errors.append(
                "Seleccionaste archivo exportado, pero no subiste ningún archivo."
            )
        else:
            content = await file.read()
            parsed = parse_bookmarks_html(content)
            bookmarks.extend(parsed)
            selected_sources.append(f"Archivo exportado ({len(parsed)} bookmarks)")

    if use_chrome:
        chrome_bookmarks, chrome_error = read_chromium_bookmarks("chrome")
        if chrome_error:
            source_errors.append(f"Chrome: {chrome_error}")
        else:
            bookmarks.extend(chrome_bookmarks)
            selected_sources.append(f"Chrome ({len(chrome_bookmarks)} bookmarks)")

    if use_edge:
        edge_bookmarks, edge_error = read_chromium_bookmarks("edge")
        if edge_error:
            source_errors.append(f"Edge: {edge_error}")
        else:
            bookmarks.extend(edge_bookmarks)
            selected_sources.append(f"Edge ({len(edge_bookmarks)} bookmarks)")

    if not bookmarks:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "request": request,
                "error": "No se cargaron bookmarks para analizar.",
                "source_errors": source_errors,
                "defaults": {
                    "target_folder": target_folder,
                    "limit": limit,
                    "skip_validation": skip_validation,
                },
            },
            status_code=400,
        )

    summary = run_analysis(
        bookmarks,
        target_folder,
        limit=parsed_limit,
        skip_validation=skip_validation,
    )

    return templates.TemplateResponse(
        request,
        "summary.html",
        {
            "request": request,
            "summary": summary,
            "source_errors": source_errors,
            "selected_sources": selected_sources,
            "target_folder": target_folder,
            "limit": parsed_limit,
            "skip_validation": skip_validation,
        },
    )


@router.get("/reports/{report_name}")
def get_report(report_name: str):
    file_path = (settings.reports_dir / report_name).resolve()
    reports_dir = settings.reports_dir.resolve()

    if reports_dir not in file_path.parents and file_path != reports_dir:
        return HTMLResponse("Reporte inválido", status_code=400)

    if not file_path.exists() or not file_path.is_file():
        return HTMLResponse("Reporte no encontrado", status_code=404)

    return FileResponse(file_path)
