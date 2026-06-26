from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from app.config import settings
from app.models.bookmark import BookmarkAnalysis


def _safe(value: str | None) -> str:
    return value or "-"


def _write_item(f, item: BookmarkAnalysis, index: int | None = None) -> None:
    prefix = f"### {index}. {item.title}" if index is not None else f"### {item.title}"
    f.write(f"{prefix}\n")
    f.write(f"- URL: {item.url}\n")
    f.write(f"- Carpeta: {_safe(item.folder_path)}\n")
    f.write(f"- Categoría: {item.category}\n")
    f.write(f"- Estado: {item.status}\n")
    if item.effective_score != item.score:
        f.write(f"- Prioridad efectiva: {item.effective_score} (local {item.score})\n")
    else:
        f.write(f"- Score: {item.score}\n")
    f.write(f"- Acción: {item.recommended_action}\n")
    f.write(f"- Duplicado: {'sí' if item.duplicate else 'no'}\n")
    f.write(f"- Motivo: {_safe(item.reason)}\n")
    if item.ai is not None:
        low = " ⚠ baja confianza" if item.ai.confidence < settings.ai_min_confidence else ""
        f.write(f"- IA · Categoría: {item.ai.category}")
        if item.ai.subcategory:
            f.write(f" / {item.ai.subcategory}")
        f.write("\n")
        f.write(f"- IA · Intención: {item.ai.intent}\n")
        f.write(f"- IA · Acción sugerida: {item.ai.recommended_action} (prioridad {item.ai.priority}, confianza {item.ai.confidence:.2f}{low})\n")
        f.write(f"- IA · Razón: {item.ai.reason}\n")
    f.write("\n")


def write_reports(reports_dir: Path, items: list[BookmarkAnalysis], schedule: dict[str, list[BookmarkAnalysis]]) -> list[str]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []

    status_counts = Counter(i.status for i in items)
    category_counts = Counter(i.category for i in items)
    action_groups: dict[str, list[BookmarkAnalysis]] = defaultdict(list)
    for item in items:
        action_groups[item.recommended_action].append(item)

    prioritized = reports_dir / "pendientes_priorizados.md"
    with prioritized.open("w", encoding="utf-8") as f:
        f.write("# Pendientes priorizados\n\n")
        f.write("## Resumen\n\n")
        f.write(f"- Total analizados: {len(items)}\n")
        f.write(f"- OK: {status_counts.get('OK', 0)}\n")
        f.write(f"- Rotos: {status_counts.get('BROKEN', 0)}\n")
        f.write(f"- Redirigidos: {status_counts.get('REDIRECTED', 0)}\n")
        f.write(f"- Forbidden: {status_counts.get('FORBIDDEN', 0)}\n")
        f.write(f"- Timeouts: {status_counts.get('TIMEOUT', 0)}\n")
        f.write(f"- Desconocidos: {status_counts.get('UNKNOWN', 0)}\n")
        f.write(f"- No validados: {status_counts.get('NOT_VALIDATED', 0)}\n")
        f.write(f"- Duplicados: {sum(1 for i in items if i.duplicate)}\n\n")

        f.write("## Categorías\n\n")
        for category, count in category_counts.most_common():
            f.write(f"- {category}: {count}\n")
        f.write("\n")

        sections = [
            ("ver_esta_semana", "Ver esta semana"),
            ("ver_luego", "Ver luego"),
            ("archivar", "Archivar"),
            ("revisar_o_borrar", "Revisar o borrar"),
            ("borrar_probable", "Borrar probable"),
        ]
        for action, title in sections:
            f.write(f"## {title}\n\n")
            group = sorted(action_groups.get(action, []), key=lambda x: x.effective_score, reverse=True)
            if not group:
                f.write("Sin elementos.\n\n")
                continue
            for idx, item in enumerate(group, start=1):
                _write_item(f, item, idx)
    files.append(prioritized.name)

    broken = reports_dir / "links_rotos.md"
    with broken.open("w", encoding="utf-8") as f:
        f.write("# Links rotos o problemáticos\n\n")
        problem_statuses = {"BROKEN", "TIMEOUT", "UNKNOWN"}
        problem_items = [i for i in items if i.status in problem_statuses]
        if not problem_items:
            f.write("No se encontraron links rotos o problemáticos.\n")
        for i in problem_items:
            f.write(f"- {i.title} | {i.status} | {i.url}\n")
    files.append(broken.name)

    duplicates = reports_dir / "duplicados.md"
    with duplicates.open("w", encoding="utf-8") as f:
        f.write("# Duplicados\n\n")
        duplicate_items = [i for i in items if i.duplicate]
        if not duplicate_items:
            f.write("No se encontraron duplicados.\n")
        for i in duplicate_items:
            f.write(f"- {i.title} - {i.normalized_url}\n  - URL: {i.url}\n")
    files.append(duplicates.name)

    chrono = reports_dir / "cronograma_7_dias.md"
    with chrono.open("w", encoding="utf-8") as f:
        f.write("# Cronograma sugerido de 7 días\n\n")
        for day, day_items in schedule.items():
            f.write(f"## {day}\n\n")
            if not day_items:
                f.write("Sin recomendación para este día.\n\n")
                continue
            for item in day_items:
                f.write(f"- {item.title}\n")
                f.write(f"  - URL: {item.url}\n")
                f.write(f"  - Carpeta: {_safe(item.folder_path)}\n")
                f.write(f"  - Categoría: {item.category}\n")
                f.write(f"  - Motivo: {_safe(item.reason)}\n")
                f.write(f"  - Prioridad: {item.effective_score}\n")
            f.write("\n")
    files.append(chrono.name)

    csv_file = reports_dir / "resultado.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title", "url", "normalized_url", "folder_path", "category", "status", "score",
                "effective_score", "recommended_action", "duplicate", "reason",
                "ai_category", "ai_intent", "ai_action", "ai_priority", "ai_confidence", "ai_reason",
            ],
        )
        writer.writeheader()
        for i in items:
            writer.writerow({
                "title": i.title,
                "url": i.url,
                "normalized_url": i.normalized_url,
                "folder_path": i.folder_path,
                "category": i.category,
                "status": i.status,
                "score": i.score,
                "effective_score": i.effective_score,
                "recommended_action": i.recommended_action,
                "duplicate": i.duplicate,
                "reason": i.reason,
                "ai_category": i.ai.category if i.ai else "",
                "ai_intent": i.ai.intent if i.ai else "",
                "ai_action": i.ai.recommended_action if i.ai else "",
                "ai_priority": i.ai.priority if i.ai else "",
                "ai_confidence": i.ai.confidence if i.ai else "",
                "ai_reason": i.ai.reason if i.ai else "",
            })
    files.append(csv_file.name)
    return files
