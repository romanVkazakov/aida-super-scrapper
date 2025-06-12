import pytest
from app.extract import smart_extract as parse

@pytest.mark.parametrize("html,expected", [
    # 1) og:title берётся приоритетно
    ("<html><head>"
     "<meta property='og:title' content='OG CONTENT'>"
     "<title>Ignored</title></head><body><h1>Ignored</h1></body></html>", 
     "OG CONTENT"),
    # 2) если og:title нет — берём <h1>
    ("<html><head><title>Ignored</title></head>"
     "<body><h1>Header Text</h1></body></html>", 
     "Header Text"),
    # 3) если ни og:title, ни h1 — fallback на <title>
    ("<html><head><title>Just Title</title></head><body></body></html>", 
     "Just Title"),
    # 4) без всего — возвращаем пустую строку
    ("<html><head></head><body></body></html>", ""),
])
def test_parse_title(html, expected):
    result = parse(html, url="http://example.com")
    assert result["title"] == expected

def test_parse_publish_date_and_text():
    sample = (
        "<html><body>"
        "<div class='publish_date'>2025-06-12</div>"
        "<div class='content'>Hello World</div>"
        "</body></html>"
    )
    res = parse(sample, url="http://x")
    assert "publish_date" in res
    assert "text" in res
    assert "Hello" in res["text"]
