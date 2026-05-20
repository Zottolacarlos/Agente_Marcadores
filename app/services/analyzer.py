from app.config import settings
from app.models.analysis import AnalysisSummary
from app.models.bookmark import Bookmark, BookmarkAnalysis
from app.repositories.sqlite_repository import SQLiteRepository
from app.services.bookmark_normalizer import normalize_url
from app.services.duplicate_detector import detect_duplicates
from app.services.link_validator import validate_url
from app.services.priority_scorer import score_bookmark
from app.services.report_generator import write_reports
from app.services.rule_classifier import classify
from app.services.scheduler import build_7_day_schedule


def run_analysis(bookmarks: list[Bookmark], target_folder: str = "Pendientes") -> AnalysisSummary:
    warning = None
    scoped = [b for b in bookmarks if target_folder.lower() in (b.folder_path or "").lower()]
    if not scoped:
        warning = f"No se encontró carpeta '{target_folder}'. Se analizaron todos los bookmarks."
        scoped = bookmarks

    normalized = [normalize_url(b.url) for b in scoped]
    duplicate_set = detect_duplicates(normalized)

    analyzed: list[BookmarkAnalysis] = []
    for b, nurl in zip(scoped, normalized):
        status = validate_url(b.url, settings.request_timeout)
        category = classify(b.title, b.url, b.folder_path)
        dup = nurl in duplicate_set
        score, action, reason = score_bookmark(category, status, b.folder_path, dup, b.title, b.url)
        analyzed.append(
            BookmarkAnalysis(
                title=b.title,
                url=b.url,
                normalized_url=nurl,
                folder_path=b.folder_path,
                status=status,
                category=category,
                score=score,
                recommended_action=action,
                duplicate=dup,
                reason=reason,
            )
        )

    analyzed_sorted = sorted(analyzed, key=lambda x: x.score, reverse=True)
    schedule = build_7_day_schedule(analyzed_sorted)
    report_files = write_reports(settings.reports_dir, analyzed_sorted, schedule)
    SQLiteRepository().save_analysis(analyzed_sorted)

    return AnalysisSummary(
        total=len(analyzed_sorted),
        ok=sum(1 for x in analyzed_sorted if x.status == "OK"),
        broken=sum(1 for x in analyzed_sorted if x.status == "BROKEN"),
        duplicates=sum(1 for x in analyzed_sorted if x.duplicate),
        review_or_delete=sum(1 for x in analyzed_sorted if x.recommended_action in {"revisar_o_borrar", "borrar_probable"}),
        top_recommended=analyzed_sorted[:10],
        reports=report_files,
        warning=warning,
    )
