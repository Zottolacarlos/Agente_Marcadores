from __future__ import annotations

from html.parser import HTMLParser

from bs4 import BeautifulSoup

from app.models.bookmark import Bookmark


UNKNOWN_FOLDER = "unknown"


class NetscapeBookmarkHTMLParser(HTMLParser):
    """
    Parser tolerante para exports Netscape Bookmark HTML de Chrome/Edge/Firefox.

    No depende de que BeautifulSoup reconstruya bien el árbol, porque los exports
    suelen tener tags sin cierre estricto: <DL><p><DT>...
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.bookmarks: list[Bookmark] = []
        self.seen: set[tuple[str, str, str]] = set()

        self.folder_stack: list[str] = []
        self.dl_folder_stack: list[bool] = []

        self.pending_folder: str | None = None

        self.capturing_h3 = False
        self.h3_parts: list[str] = []

        self.capturing_a = False
        self.a_parts: list[str] = []
        self.current_href: str | None = None
        self.current_add_date: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value for key, value in attrs if key}

        if tag == "dl":
            if self.pending_folder:
                self.folder_stack.append(self.pending_folder)
                self.dl_folder_stack.append(True)
                self.pending_folder = None
            else:
                self.dl_folder_stack.append(False)
            return

        if tag == "h3":
            self.capturing_h3 = True
            self.h3_parts = []
            return

        if tag == "a":
            href = attrs_dict.get("href")
            if not href:
                return

            self.capturing_a = True
            self.a_parts = []
            self.current_href = href
            self.current_add_date = attrs_dict.get("add_date")
            return

    def handle_data(self, data: str) -> None:
        if self.capturing_h3:
            self.h3_parts.append(data)

        if self.capturing_a:
            self.a_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "h3":
            folder_name = "".join(self.h3_parts).strip()
            if folder_name:
                self.pending_folder = folder_name

            self.capturing_h3 = False
            self.h3_parts = []
            return

        if tag == "a":
            self._finish_bookmark()
            return

        if tag == "dl":
            if self.dl_folder_stack:
                pushed_folder = self.dl_folder_stack.pop()
                if pushed_folder and self.folder_stack:
                    self.folder_stack.pop()
            return

    def close(self) -> None:
        if self.capturing_a:
            self._finish_bookmark()
        super().close()

    def _finish_bookmark(self) -> None:
        if not self.current_href:
            self._reset_current_bookmark()
            return

        title = "".join(self.a_parts).strip() or self.current_href
        folder_path = "/".join(self.folder_stack) if self.folder_stack else UNKNOWN_FOLDER

        bookmark = Bookmark(
            title=title,
            url=self.current_href,
            folder_path=folder_path,
            added_at=self.current_add_date,
            browser_source="html_export",
        )

        key = (bookmark.url, bookmark.folder_path, bookmark.title)
        if key not in self.seen:
            self.seen.add(key)
            self.bookmarks.append(bookmark)

        self._reset_current_bookmark()

    def _reset_current_bookmark(self) -> None:
        self.capturing_a = False
        self.a_parts = []
        self.current_href = None
        self.current_add_date = None


def parse_bookmarks_html(file_content: bytes) -> list[Bookmark]:
    parser = NetscapeBookmarkHTMLParser()
    parser.feed(file_content.decode("utf-8", errors="ignore"))
    parser.close()

    if parser.bookmarks:
        return parser.bookmarks

    # Fallback defensivo: si el parser por eventos no encontró nada,
    # al menos recuperar todos los anchors.
    soup = BeautifulSoup(file_content, "html.parser")
    results: list[Bookmark] = []
    seen: set[tuple[str, str, str]] = set()

    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if not href:
            continue

        bookmark = Bookmark(
            title=a_tag.get_text(strip=True) or href,
            url=href,
            folder_path=UNKNOWN_FOLDER,
            added_at=a_tag.get("add_date"),
            browser_source="html_export",
        )

        key = (bookmark.url, bookmark.folder_path, bookmark.title)
        if key not in seen:
            seen.add(key)
            results.append(bookmark)

    return results