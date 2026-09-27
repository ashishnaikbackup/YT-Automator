from __future__ import annotations

import html
import re
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def _clean(value: str) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()


def search_news(query: str, limit: int = 8) -> list[dict]:
    """Collect recent Google News RSS headlines without requiring an API key."""
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    request = Request(url, headers={"User-Agent": "YT-Automator/1.0"})
    with urlopen(request, timeout=12) as response:
        root = ET.fromstring(response.read())

    results = []
    for item in root.findall("./channel/item")[:limit]:
        title = _clean(item.findtext("title"))
        link = _clean(item.findtext("link"))
        pub_date = _clean(item.findtext("pubDate"))
        source = item.find("source")
        source_name = _clean(source.text if source is not None else "")
        if title:
            results.append({"title": title, "url": link, "published": pub_date, "source": source_name})
    return results


def format_research(results: list[dict]) -> str:
    lines = []
    for i, item in enumerate(results, 1):
        lines.append(f"{i}. {item['title']} — {item['source']} — {item['published']}\n   {item['url']}")
    return "\n".join(lines)
