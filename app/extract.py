from app.log_config import init_logging
init_logging(__name__)
import json, re
from bs4 import BeautifulSoup
from trafilatura import extract, fetch_url
from newspaper import Article
from readability import Document
from lxml import html as lh

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

def _title_date_from_html(raw_html: str):
    """Ищем title и дату в <meta>, <title> и JSON-LD."""
    soup = BeautifulSoup(raw_html, "lxml")

    # ----- TITLE -----
    title = soup.title.string.strip() if soup.title else None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = og["content"].strip()

    # ----- DATE в <meta> -----
    date = None
    for attr in ("article:published_time", "og:published_time",
                 "publishdate", "pubdate"):
        tag = soup.find("meta", attrs={"property": attr}) or \
              soup.find("meta", attrs={"name": attr})
        if tag and tag.get("content") and DATE_RE.search(tag["content"]):
            date = DATE_RE.search(tag["content"]).group(0)
            break

    # ----- DATE в JSON-LD -----
    if not date:
        for ld in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(ld.string)
            except Exception:
                continue
            if isinstance(data, list):
                data = data[0]
            for key in ("datePublished", "dateModified", "uploadDate"):
                if key in data and DATE_RE.search(data[key]):
                    date = DATE_RE.search(data[key]).group(0)
                    break
            if date:
                break

    return title or "", date

def smart_extract(url: str, raw_html: str):
    if not raw_html:
        raw_html = fetch_url(url)

    # 1) Trafilatura
    doc_str = extract(raw_html, output_format="json")
    if doc_str:
        j = json.loads(doc_str)
        title = j.get("title")
        date  = j.get("date")
        if not title or not date:
            t2, d2 = _title_date_from_html(raw_html)
            title = title or t2
            date  = date  or d2
        return {"url": url, "title": title, "publish_date": date, "text": j.get("text")}

    # 2) Newspaper3k
    try:
        art = Article(url); art.download(input_html=raw_html); art.parse()
        title, date = art.title, art.publish_date
        if not title or not date:
            t2, d2 = _title_date_from_html(raw_html)
            title = title or t2
            date  = date  or d2
        return {
            "url": url,
            "title": title,
            "publish_date": str(date) if date else None,
            "text": art.text,
        }
    except Exception:
        pass

    # 3) Readability fallback
    doc = Document(raw_html)
    tree = lh.fromstring(doc.summary())
    text = " ".join(tree.xpath("//text()"))
    t2, d2 = _title_date_from_html(raw_html)
    return {"url": url, "title": t2 or doc.title(), "publish_date": d2, "text": text}
