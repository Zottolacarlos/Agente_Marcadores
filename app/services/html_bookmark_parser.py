from bs4 import BeautifulSoup
from app.models.bookmark import Bookmark


def parse_bookmarks_html(file_content: bytes) -> list[Bookmark]:
    soup = BeautifulSoup(file_content, "html.parser")
    results: list[Bookmark] = []

    def walk_dl(dl_tag, parents: list[str]) -> None:
        if not dl_tag:
            return
        for dt in dl_tag.find_all("dt", recursive=False):
            h3 = dt.find("h3", recursive=False)
            a = dt.find("a", recursive=False)
            if h3:
                nested = dt.find_next_sibling("dl")
                walk_dl(nested, parents + [h3.get_text(strip=True)])
            elif a and a.get("href"):
                results.append(
                    Bookmark(
                        title=a.get_text(strip=True) or a.get("href"),
                        url=a["href"],
                        folder_path="/".join(parents),
                        added_at=a.get("add_date"),
                        browser_source="html_export",
                    )
                )

    root_dl = soup.find("dl")
    walk_dl(root_dl, [])
    return results
