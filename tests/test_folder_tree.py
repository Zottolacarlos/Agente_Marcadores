from app.models.bookmark import Bookmark
from app.services.folder_tree import build_folder_tree


def _bookmarks():
    return [
        Bookmark(title="A", url="https://a.com", folder_path="Barra de marcadores/Games"),
        Bookmark(title="B", url="https://b.com", folder_path="Barra de marcadores/Games/Deseados/Libros"),
        Bookmark(title="C", url="https://c.com", folder_path="Barra de marcadores/IMSA"),
    ]


def test_tree_is_nested_with_recursive_counts():
    tree = build_folder_tree(_bookmarks())
    assert len(tree) == 1  # raíz: "Barra de marcadores"
    root = tree[0]
    assert root["name"] == "Barra de marcadores"
    assert root["count"] == 3  # todo cuelga de la raíz

    games = next(c for c in root["children"] if c["name"] == "Games")
    assert games["count"] == 2  # el directo + el de la subcarpeta
    assert games["path"] == "Barra de marcadores/Games"

    deseados = next(c for c in games["children"] if c["name"] == "Deseados")
    assert deseados["count"] == 1
    libros = deseados["children"][0]
    assert libros["name"] == "Libros"
    assert libros["path"] == "Barra de marcadores/Games/Deseados/Libros"


def test_tree_strips_chromium_profile_prefix():
    bks = [Bookmark(title="X", url="https://x.com", folder_path="Default/Barra/IA")]
    tree = build_folder_tree(bks)
    assert tree[0]["name"] == "Barra"
