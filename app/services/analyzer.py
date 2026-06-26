from app.config import settings
from app.models.analysis import AnalysisSummary
from app.models.bookmark import Bookmark, BookmarkAnalysis
from app.repositories.sqlite_repository import SQLiteRepository
from app.services import ai_classifier
from app.services.bookmark_normalizer import normalize_url
from app.services.duplicate_detector import detect_duplicates
from app.services.link_validator import validate_url
from app.services.priority_scorer import action_from_score, score_bookmark
from app.services.report_generator import write_reports
from app.services.rule_classifier import classify
from app.services.scheduler import build_7_day_schedule

NOT_VALIDATED = "NOT_VALIDATED"


def run_analysis(
    bookmarks: list[Bookmark],
    target_folder: str = "Pendientes",
    *,
    limit: int | None = None,
    skip_validation: bool = False,
    use_ai: bool = False,
) -> AnalysisSummary:
    warning = None
    folder_filter = (target_folder or "").strip().lower()

    if folder_filter:
        scoped = [b for b in bookmarks if folder_filter in (b.folder_path or "").lower()]
    else:
        scoped = bookmarks

    if folder_filter and not scoped:
        warning = f"No se encontró carpeta '{target_folder}'. Se analizaron todos los bookmarks."
        scoped = bookmarks

    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser mayor o igual a 1")
        scoped = scoped[:limit]

    normalized = [normalize_url(b.url) for b in scoped]
    duplicate_set = detect_duplicates(normalized)

    analyzed: list[BookmarkAnalysis] = []
    for b, nurl in zip(scoped, normalized):
        status = NOT_VALIDATED if skip_validation else validate_url(b.url, settings.request_timeout)
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
                effective_score=score,
            )
        )

    analyzed_sorted = sorted(analyzed, key=lambda x: x.score, reverse=True)

    # Capa IA opcional. Adjunta su criterio en item.ai y, si la confianza supera el
    # umbral, hace BLENDING: fusiona score local + prioridad IA en effective_score,
    # que pasa a mandar orden y acción. El score local queda intacto como referencia.
    ai_used = False
    ai_enriched = 0
    ai_low_confidence = 0
    if use_ai:
        if ai_classifier.is_ai_available():
            ai_used = True
            w = settings.ai_blend_weight
            for item in analyzed_sorted[: settings.ai_max_bookmarks]:
                result = ai_classifier.classify_bookmark_with_ai(
                    ai_classifier.build_payload(
                        title=item.title,
                        url=item.url,
                        folder_path=item.folder_path,
                        status=item.status,
                        rule_category=item.category,
                        rule_score=item.score,
                    )
                )
                if result is None:
                    continue
                item.ai = result
                ai_enriched += 1
                if result.confidence < settings.ai_min_confidence:
                    ai_low_confidence += 1
                    continue  # IA dudosa: no se mezcla, manda el local.
                blended = round((1 - w) * item.score + w * result.priority)
                item.effective_score = max(0, min(100, blended))
                item.recommended_action = action_from_score(
                    item.effective_score, item.status, item.duplicate
                )
            # Re-ordenar por el score efectivo (ya con el criterio IA aplicado).
            analyzed_sorted.sort(key=lambda x: x.effective_score, reverse=True)
        else:
            ai_warning = "IA solicitada, pero no está disponible (falta OPENAI_API_KEY o el cliente). Se usó análisis local."
            warning = f"{warning} {ai_warning}".strip() if warning else ai_warning

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
        ai_used=ai_used,
        ai_enriched=ai_enriched,
        ai_low_confidence=ai_low_confidence,
    )
