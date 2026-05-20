from app.services.html_bookmark_parser import parse_bookmarks_html


def test_parse_bookmarks_html_netscape_structure():
    html = b'''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<HTML><BODY>
<DL><p>
  <DT><H3>Barra de favoritos</H3>
  <DL><p>
    <DT><H3>Pendientes</H3>
    <DL><p>
      <DT><A HREF="https://example.com/a" ADD_DATE="123">Articulo A</A>
      <DT><A HREF="https://example.com/b">Articulo B</A>
    </DL><p>
    <DT><H3>Lectura</H3>
    <DL><p>
      <DT><A HREF="https://news.example.com/c">Noticia C</A>
    </DL><p>
  </DL><p>
</DL><p>
</BODY></HTML>'''

    rows = parse_bookmarks_html(html)

    assert len(rows) > 0
    assert len(rows) == 3

    pending_rows = [r for r in rows if "pendientes" in r.folder_path.lower()]
    assert len(pending_rows) == 2

    first = pending_rows[0]
    assert first.url == "https://example.com/a"
    assert first.title == "Articulo A"
    assert first.added_at == "123"
    assert first.folder_path == "Barra de favoritos/Pendientes"


def test_parse_bookmarks_html_uppercase_and_unknown_folder_fallback():
    html = b'''<DL><DT><A HREF="https://example.org">Link</A></DT></DL>'''
    rows = parse_bookmarks_html(html)

    assert len(rows) == 1
    assert rows[0].folder_path == "unknown"
    assert rows[0].url == "https://example.org"
