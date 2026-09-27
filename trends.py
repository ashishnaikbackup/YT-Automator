from __future__ import annotations

from research import search_news

DEFAULT_QUERIES = [
    "AI artificial intelligence",
    "technology startups gadgets",
    "Python programming coding",
    "engineering semiconductor chips",
]


def discover_topics(limit_per_query: int = 5) -> list[dict]:
    topics = []
    seen = set()
    for query in DEFAULT_QUERIES:
        try:
            results = search_news(query, limit_per_query)
        except Exception:
            continue
        for item in results:
            key = item["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            topics.append({"topic": item["title"], "source": item["source"], "url": item["url"], "published": item["published"]})
    return topics
