from __future__ import annotations

from collections import Counter

from app.models.bookmark import Bookmark

# Segmentos raíz que no aportan al usuario al elegir carpeta (los inyecta el
# lector de Chromium: el primer nivel es el nombre del perfil).
_ROOT_NOISE = {"default"}


def _clean_segments(folder_path: str | None) -> list[str]:
    segments = [s.strip() for s in (folder_path or "").split("/") if s.strip()]
    if segments:
        first = segments[0].lower()
        if first in _ROOT_NOISE or first.startswith("profile "):
            segments = segments[1:]
    return segments


def extract_folder_tree(bookmarks: list[Bookmark], max_level: int = 2) -> list[dict]:
    """
    Devuelve las carpetas de 1er y 2do nivel presentes en los marcadores, con
    cuántos marcadores cuelgan de cada prefijo. Pensado para sugerirle al usuario
    qué carpeta analizar sin que tenga que recordar su estructura de favoritos.
    """
    counts: Counter[tuple[str, ...]] = Counter()
    for bookmark in bookmarks:
        segments = _clean_segments(bookmark.folder_path)
        if not segments:
            continue
        for depth in range(1, min(max_level, len(segments)) + 1):
            counts[tuple(segments[:depth])] += 1

    folders = [
        {"path": "/".join(prefix), "level": len(prefix), "count": count}
        for prefix, count in counts.items()
    ]
    # Las carpetas más pobladas primero (suele ser donde está lo pendiente),
    # con el path como desempate estable.
    folders.sort(key=lambda f: (-f["count"], f["level"], f["path"].lower()))
    return folders


def build_folder_tree(bookmarks: list[Bookmark]) -> list[dict]:
    """
    Devuelve el árbol COMPLETO de carpetas anidado para mostrarlo navegable en la UI.
    Cada nodo: {name, path, count, children}. `count` = total de marcadores bajo esa
    carpeta (incluyendo subcarpetas), que es justo lo que se analiza al elegirla.
    """
    roots: dict[str, dict] = {}

    for bookmark in bookmarks:
        segments = _clean_segments(bookmark.folder_path)
        if not segments:
            continue
        children_map = roots
        parts: list[str] = []
        for segment in segments:
            parts.append(segment)
            node = children_map.get(segment)
            if node is None:
                node = {"name": segment, "path": "/".join(parts), "count": 0, "_children": {}}
                children_map[segment] = node
            node["count"] += 1
            children_map = node["_children"]

    def _to_list(children_map: dict[str, dict]) -> list[dict]:
        nodes = sorted(children_map.values(), key=lambda n: (-n["count"], n["name"].lower()))
        return [
            {
                "name": n["name"],
                "path": n["path"],
                "count": n["count"],
                "children": _to_list(n["_children"]),
            }
            for n in nodes
        ]

    return _to_list(roots)
