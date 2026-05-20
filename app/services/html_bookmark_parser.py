from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from app.models.bookmark import Bookmark


UNKNOWN_FOLDER = "unknown"


def parse_bookmarks_html(file_content: bytes) -> list[Bookmark]:
    """Parse Netscape Bookmark HTML (Chrome/Edge/Firefox exports)."""
    soup = BeautifulSoup(file_content, "html.parser")
    results: list[Bookmark] = []
    seen: set[tuple[str, str, str]] = set()

    def add_result(bookmark: Bookmark) -> None:
        key = (bookmark.url, bookmark.folder_path, bookmark.title)
        if key not in seen:
            seen.add(key)
            results.append(bookmark)

    def build_bookmark(a_tag: Tag, folder_stack: list[str]) -> Bookmark | None:
        href = a_tag.get("href")
        if not href:
            return None

        folder_path = "/".join(folder_stack) if folder_stack else UNKNOWN_FOLDER
        return Bookmark(
            title=a_tag.get_text(strip=True) or href,
            url=href,
            folder_path=folder_path,
            added_at=a_tag.get("add_date"),
            browser_source="html_export",
        )

    def process_dt(dt_tag: Tag, folder_stack: list[str]) -> None:
        direct_a = dt_tag.find("a", recursive=False)
        if direct_a is not None:
            bookmark = build_bookmark(direct_a, folder_stack)
            if bookmark:
                add_result(bookmark)
            return

        direct_h3 = dt_tag.find("h3", recursive=False)
        if direct_h3 is None:
            return

        folder_name = direct_h3.get_text(strip=True)
        if not folder_name:
            return

        nested_dl = dt_tag.find("dl", recursive=False)
        sibling_dl = dt_tag.find_next_sibling(lambda t: isinstance(t, Tag) and (t.name or "").lower() == "dl")
        target_dl = nested_dl or sibling_dl
        if target_dl is not None:
            walk_dl(target_dl, folder_stack + [folder_name])

    def walk_dl(dl_tag: Tag, folder_stack: list[str]) -> None:
        for child in dl_tag.children:
            if not isinstance(child, Tag):
                continue

            child_name = (child.name or "").lower()
            if child_name == "dt":
                process_dt(child, folder_stack)
            elif child_name == "p":
                walk_dl(child, folder_stack)

    root_dl = soup.find("dl")
    if root_dl is not None:
        walk_dl(root_dl, [])

    if not results:
        for a_tag in soup.find_all("a"):
            bookmark = build_bookmark(a_tag, [])
            if bookmark:
                add_result(bookmark)

    return results
