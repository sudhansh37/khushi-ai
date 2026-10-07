"""Free web research — DuckDuckGo + Wikipedia fallback. No API key required."""
import asyncio
import json
import re
import urllib.parse
import urllib.request


def _ddgs_search(query, max_results):
    # The library was renamed from `duckduckgo_search` to `ddgs`.
    try:
        from ddgs import DDGS
    except Exception:  # pragma: no cover - fallback for older installs
        from duckduckgo_search import DDGS

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title") or "",
                    "url": r.get("href") or r.get("url") or "",
                    "snippet": r.get("body") or r.get("snippet") or "",
                }
            )
    return results


def _wikipedia_search(query, max_results=3):
    """Key-free Wikipedia lookup — reliable from cloud / datacenter IPs."""
    out = []
    try:
        qs = urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": str(max_results),
            }
        )
        req = urllib.request.Request(
            f"https://en.wikipedia.org/w/api.php?{qs}",
            headers={"User-Agent": "KhushiAI/1.0 (open-source chatbot)"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        for hit in data.get("query", {}).get("search", []):
            title = hit.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", hit.get("snippet", ""))
            out.append(
                {
                    "title": f"Wikipedia: {title}",
                    "url": "https://en.wikipedia.org/wiki/"
                    + urllib.parse.quote(title.replace(" ", "_")),
                    "snippet": snippet,
                }
            )
    except Exception:
        pass
    return out


async def web_search(query, max_results=5):
    """DuckDuckGo first; fall back to Wikipedia if DDG is empty or blocked."""
    results = []
    try:
        results = await asyncio.to_thread(_ddgs_search, query, max_results)
    except Exception:
        results = []
    if not results:
        results = await asyncio.to_thread(_wikipedia_search, query, max_results)
    return results


def format_context(results):
    """Flatten search results into a compact block for the prompt."""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']} — {r['url']}\n{r['snippet']}")
    return "\n\n".join(lines)
