from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from app.models.bookmark import Bookmark


UNKNOWN_FOLDER = "unknown"


def parse_bookmarks_html(file_content: bytes) -> list[Bookmark]:
    """Parse Netscape Bookmark HTML (Chrome/Edge/Firefox exports)."""
    soup = BeautifulSoup(file_content, "html.parser")
    results: list[Bookmark] = []

    root_dls = soup.find_all("dl")
    if not root_dls:
        return results

    def walk_dl(dl_tag: Tag, folder_stack: list[str]) -> None:
        for child in dl_tag.children:
            if not isinstance(child, Tag):
                continue

            if child.name and child.name.lower() == "dt":
                _process_dt(child, folder_stack)
                continue

            if child.name and child.name.lower() == "dl":
                walk_dl(child, folder_stack)

    def _process_dt(dt_tag: Tag, folder_stack: list[str]) -> None:
        # Bookmark entry
        a_tag = dt_tag.find("a", recursive=False)
        if a_tag is not None:
            href = a_tag.get("href")
            if href:
                title = a_tag.get_text(strip=True) or href
                folder_path = "/".join(folder_stack) if folder_stack else UNKNOWN_FOLDER
                results.append(
                    Bookmark(
                        title=title,
                        url=href,
                        folder_path=folder_path,
                        added_at=a_tag.get("add_date"),
                        browser_source="html_export",
                    )
                )
            return

        # Folder entry with nested DL
        h3_tag = dt_tag.find("h3", recursive=False)
        if h3_tag is None:
            return

        folder_name = h3_tag.get_text(strip=True)
        next_dl = dt_tag.find_next_sibling(lambda t: isinstance(t, Tag) and t.name and t.name.lower() == "dl")
        if next_dl is not None:
            walk_dl(next_dl, folder_stack + [folder_name])

    # Start from first root DL (Netscape files typically have one root tree)
    walk_dl(root_dls[0], [])
    return results
