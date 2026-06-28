from app.models.bookmark import Bookmark
from app.services import analyzer


def _bookmarks():
    return [
        Bookmark(title="A", url="https://a.com", folder_path="Barra de marcadores/Games"),
        Bookmark(title="B", url="https://b.com", folder_path="Barra de marcadores/Games/Deseados/Libros"),
        Bookmark(title="C", url="https://c.com", folder_path="Barra de marcadores/IMSA"),
    ]


def test_trailing_slash_still_includes_direct_folder_items():
    # "Games/" con barra final no debe excluir los items directos en Games.
    summary = analyzer.run_analysis(_bookmarks(), "Barra de marcadores/Games/", skip_validation=True)
    assert summary.total == 2  # el directo + el de la subcarpeta


def test_folder_filter_includes_whole_subtree():
    summary = analyzer.run_analysis(_bookmarks(), "Games", skip_validation=True)
    assert summary.total == 2


def test_multiple_folders_selected():
    # Multi-selección: varias carpetas (una por línea) → matchea cualquiera.
    summary = analyzer.run_analysis(_bookmarks(), "Games\nIMSA", skip_validation=True)
    assert summary.total == 3  # 2 de Games + 1 de IMSA


def test_blank_lines_in_selection_are_ignored():
    summary = analyzer.run_analysis(_bookmarks(), "\n  \nIMSA\n", skip_validation=True)
    assert summary.total == 1
