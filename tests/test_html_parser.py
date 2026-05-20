from app.services.html_bookmark_parser import parse_bookmarks_html


def test_parse_bookmarks_html_netscape_clear_structure_preserves_folder_path():
    html = b'''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<HTML><BODY>
<DL>
  <DT><H3>Barra de favoritos</H3></DT>
  <DL>
    <DT><H3>Pendientes</H3></DT>
    <DL>
      <DT><A HREF="https://example.com/a" ADD_DATE="123">Articulo A</A></DT>
      <DT><A HREF="https://example.com/b">Articulo B</A></DT>
    </DL>
    <DT><H3>Lectura</H3></DT>
    <DL>
      <DT><A HREF="https://news.example.com/c">Noticia C</A></DT>
    </DL>
  </DL>
</DL>
</BODY></HTML>'''

    rows = parse_bookmarks_html(html)
    assert len(rows) == 3

    pending_rows = [r for r in rows if "pendientes" in r.folder_path.lower()]
    assert len(pending_rows) == 2
    assert pending_rows[0].added_at == "123"


def test_parse_bookmarks_html_netscape_unclosed_tags_returns_non_zero():
    html = b'''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
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
</DL><p>'''

    rows = parse_bookmarks_html(html)
    assert len(rows) > 0


def test_parse_bookmarks_html_with_links_outside_dl_uses_fallback_unknown_folder():
    html = b'''<HTML><BODY><A HREF="https://one.example">One</A><A HREF="https://two.example">Two</A></BODY></HTML>'''
    rows = parse_bookmarks_html(html)

    assert len(rows) > 0
    assert len(rows) == 2
    assert all(row.folder_path == "unknown" for row in rows)


def test_parse_bookmarks_html_uppercase_tag_names_and_attributes():
    html = b'''<DL><p><DT><A HREF="https://example.org" ADD_DATE="456">Link</A></DL>'''
    rows = parse_bookmarks_html(html)

    assert len(rows) == 1
    assert rows[0].folder_path == "unknown"
    assert rows[0].url == "https://example.org"
    assert rows[0].added_at == "456"
