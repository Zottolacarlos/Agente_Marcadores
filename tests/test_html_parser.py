from app.services.html_bookmark_parser import parse_bookmarks_html


def test_parse_bookmarks_html():
    html = b'''<DL><DT><H3>Pendientes</H3></DT><DL><DT><A HREF="https://example.com" ADD_DATE="123">Example</A></DT></DL></DL>'''
    rows = parse_bookmarks_html(html)
    assert len(rows) == 1
    assert rows[0].folder_path == "Pendientes"
