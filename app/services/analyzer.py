import logging
from collections import Counter
from datetime import datetime

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

logger = logging.getLogger("app.analyzer")

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
    logger.info(
        ">> run_analysis: %d bookmarks de entrada | carpeta=%r | limit=%s | skip_validation=%s | use_ai=%s",
        len(bookmarks), target_folder, limit, skip_validation, use_ai,
    )
    # `target_folder` puede traer VARIAS carpetas (una por línea) para multi-selección.
    # Se normalizan las barras sobrantes en ambos lados: elegir "Games/" (con barra
    # final) no debe excluir los marcadores que están directamente en "Games".
    folder_filters = [
        f.strip().strip("/").lower()
        for f in (target_folder or "").splitlines()
        if f.strip().strip("/")
    ]

    if folder_filters:
        scoped = [
            b for b in bookmarks
            if any(ff in (b.folder_path or "").strip("/").lower() for ff in folder_filters)
        ]
    else:
        scoped = bookmarks

    logger.info("Filtros %s -> %d/%d bookmarks en alcance", folder_filters or "(ninguno)", len(scoped), len(bookmarks))
    if scoped:
        folder_counts = Counter(b.folder_path for b in scoped)
        muestra = " | ".join(f"{path} ({n})" for path, n in folder_counts.most_common(8))
        logger.info("Carpetas en alcance (top): %s", muestra)

    if folder_filters and not scoped:
        warning = f"No se encontró ninguna de las carpetas {folder_filters}. Se analizaron todos los bookmarks."
        logger.warning("Filtros %s no matchearon nada -> se analiza TODO (%d)", folder_filters, len(bookmarks))
        scoped = bookmarks

    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser mayor o igual a 1")
        before = len(scoped)
        scoped = scoped[:limit]
        logger.info("Limite aplicado: %d -> %d (se recortaron %d)", limit, len(scoped), before - len(scoped))

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
    logger.info("Categorias (local): %s", dict(Counter(x.category for x in analyzed_sorted).most_common()))

    # Capa IA opcional. Adjunta su criterio en item.ai y, si la confianza supera el
    # umbral, hace BLENDING: fusiona score local + prioridad IA en effective_score,
    # que pasa a mandar orden y acción. El score local queda intacto como referencia.
    ai_used = False
    ai_enriched = 0
    ai_low_confidence = 0
    if use_ai:
        if ai_classifier.is_ai_available():
            ai_used = True
            targets = analyzed_sorted[: settings.ai_max_bookmarks]
            if len(analyzed_sorted) > settings.ai_max_bookmarks:
                logger.warning("IA: %d analizados > tope AI_MAX_BOOKMARKS=%d; se enriquecen los primeros %d por score local", len(analyzed_sorted), settings.ai_max_bookmarks, len(targets))
            logger.info("IA disponible. Clasificando %d bookmarks en lotes de %d...", len(targets), settings.ai_batch_size)
            payloads = [
                ai_classifier.build_payload(
                    title=item.title,
                    url=item.url,
                    folder_path=item.folder_path,
                    status=item.status,
                    rule_category=item.category,
                    rule_score=item.score,
                )
                for item in targets
            ]
            results = ai_classifier.classify_bookmarks_batch(payloads)
            w = settings.ai_blend_weight
            for item, result in zip(targets, results):
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
            logger.info("IA: enriquecidos=%d |baja_confianza(<%.2f)=%d", ai_enriched, settings.ai_min_confidence, ai_low_confidence)
        else:
            ai_warning = "IA solicitada, pero no está disponible (falta OPENAI_API_KEY o el cliente). Se usó análisis local."
            logger.warning("IA solicitada pero NO disponible (falta OPENAI_API_KEY?). Fallback a reglas locales.")
            warning = f"{warning} {ai_warning}".strip() if warning else ai_warning

    # Distribución final: ayuda a ver si el análisis quedó "todo archivar" y por qué.
    scores = [x.effective_score for x in analyzed_sorted]
    buckets = Counter("70-100" if s >= 70 else "45-69" if s >= 45 else "25-44" if s >= 25 else "0-24" for s in scores)
    logger.info("Acciones: %s", dict(Counter(x.recommended_action for x in analyzed_sorted)))
    logger.info("Score efectivo por rango: %s", dict(buckets))

    schedule = build_7_day_schedule(analyzed_sorted)
    report_files = write_reports(settings.reports_dir, analyzed_sorted, schedule)
    logger.info("OK Analisis listo: %d analizados | reportes en %s", len(analyzed_sorted), settings.reports_dir)

    summary = AnalysisSummary(
        total=len(analyzed_sorted),
        ok=sum(1 for x in analyzed_sorted if x.status == "OK"),
        broken=sum(1 for x in analyzed_sorted if x.status == "BROKEN"),
        duplicates=sum(1 for x in analyzed_sorted if x.duplicate),
        review_or_delete=sum(1 for x in analyzed_sorted if x.recommended_action in {"revisar_o_borrar", "borrar_probable"}),
        top_recommended=analyzed_sorted[:25],
        schedule=schedule,
        reports=report_files,
        warning=warning,
        ai_used=ai_used,
        ai_enriched=ai_enriched,
        ai_low_confidence=ai_low_confidence,
    )

    repo = SQLiteRepository()
    repo.save_analysis(analyzed_sorted)
    # Persistir el estado para el dashboard (última corrida, no historial).
    params = {
        "target_folder": target_folder,
        "limit": limit,
        "skip_validation": skip_validation,
        "use_ai": use_ai,
    }
    repo.save_state(summary, params, datetime.now().isoformat(timespec="seconds"))

    return summary
