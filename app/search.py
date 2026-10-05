"""Free web research — DuckDuckGo, no API key required."""
import asyncio


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


async def web_search(query, max_results=5):
    """Run a DuckDuckGo search off the event loop and return a list of dicts."""
    try:
        return await asyncio.to_thread(_ddgs_search, query, max_results)
    except Exception:
        return []


def format_context(results):
    """Flatten search results into a compact block for the prompt."""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']} — {r['url']}\n{r['snippet']}")
    return "\n\n".join(lines)
