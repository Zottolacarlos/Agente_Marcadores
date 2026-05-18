import csv
from pathlib import Path
from app.models.bookmark import BookmarkAnalysis


def write_reports(reports_dir: Path, items: list[BookmarkAnalysis], schedule: dict[str, list[BookmarkAnalysis]]) -> list[str]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    files = []

    prioritized = reports_dir / "pendientes_priorizados.md"
    with prioritized.open("w", encoding="utf-8") as f:
        f.write("# Pendientes priorizados\n\n")
        for i in sorted(items, key=lambda x: x.score, reverse=True):
            f.write(f"- [{i.title}]({i.url}) | {i.category} | score={i.score} | accion={i.recommended_action}\n")
    files.append(prioritized.name)

    broken = reports_dir / "links_rotos.md"
    with broken.open("w", encoding="utf-8") as f:
        f.write("# Links rotos\n\n")
        for i in items:
            if i.status == "BROKEN":
                f.write(f"- {i.title} - {i.url}\n")
    files.append(broken.name)

    duplicates = reports_dir / "duplicados.md"
    with duplicates.open("w", encoding="utf-8") as f:
        f.write("# Duplicados\n\n")
        for i in items:
            if i.duplicate:
                f.write(f"- {i.title} - {i.url}\n")
    files.append(duplicates.name)

    chrono = reports_dir / "cronograma_7_dias.md"
    with chrono.open("w", encoding="utf-8") as f:
        f.write("# Cronograma sugerido\n\n")
        for day, day_items in schedule.items():
            f.write(f"## {day}\n")
            for item in day_items:
                f.write(f"- {item.title}\n  - URL: {item.url}\n  - Motivo: {item.reason}\n  - Categoría: {item.category}\n  - Prioridad: {item.score}\n")
            f.write("\n")
    files.append(chrono.name)

    csv_file = reports_dir / "resultado.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "category", "status", "score", "recommended_action", "duplicate"])
        writer.writeheader()
        for i in items:
            writer.writerow({
                "title": i.title,
                "url": i.url,
                "category": i.category,
                "status": i.status,
                "score": i.score,
                "recommended_action": i.recommended_action,
                "duplicate": i.duplicate,
            })
    files.append(csv_file.name)
    return files
