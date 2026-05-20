import json
import os
from pathlib import Path
from app.models.bookmark import Bookmark


BROWSERS = {
    "chrome": r"AppData/Local/Google/Chrome/User Data",
    "edge": r"AppData/Local/Microsoft/Edge/User Data",
}


def _extract_nodes(node: dict, folder: list[str], source: str, out: list[Bookmark]) -> None:
    if node.get("type") == "url":
        out.append(
            Bookmark(
                title=node.get("name", "(sin título)"),
                url=node.get("url", ""),
                folder_path="/".join(folder),
                added_at=node.get("date_added"),
                browser_source=source,
            )
        )
    for child in node.get("children", []) or []:
        next_folder = folder + [node.get("name", "")]
        _extract_nodes(child, next_folder, source, out)


def read_chromium_bookmarks(browser: str) -> tuple[list[Bookmark], str | None]:
    browser = browser.lower()
    base = BROWSERS.get(browser)
    if not base:
        return [], f"Browser no soportado: {browser}"
    user_home = Path(os.path.expanduser("~"))
    profiles_root = user_home / base
    if not profiles_root.exists():
        return [], f"No se encontró instalación de {browser} en {profiles_root}"

    all_bookmarks: list[Bookmark] = []
    profile_dirs = [p for p in profiles_root.iterdir() if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile "))]
    for profile in profile_dirs:
        bfile = profile / "Bookmarks"
        if not bfile.exists():
            continue
        payload = json.loads(bfile.read_text(encoding="utf-8"))
        roots = payload.get("roots", {})
        for _, root in roots.items():
            if isinstance(root, dict):
                _extract_nodes(root, [profile.name], browser, all_bookmarks)

    if not all_bookmarks:
        return [], f"No se encontraron bookmarks para perfiles de {browser}"
    return all_bookmarks, None
