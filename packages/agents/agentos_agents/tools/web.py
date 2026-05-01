from __future__ import annotations

import os
import re
from collections.abc import Awaitable, Callable
from html import unescape
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse


class WebSearchTool:
    """Web search adapter for agents.

    Defaults to DuckDuckGo's HTML endpoint (`html.duckduckgo.com/html/`),
    which returns real ranked results without requiring an API key. The
    Instant-Answer JSON API was tried first but only returns Wikipedia-style
    abstracts, so it's useless for current events ("Champions semis 2026"
    and friends).

    Set `WEB_SEARCH_PROVIDER=tavily` plus `TAVILY_API_KEY` to upgrade to
    Tavily (better recall, requires signup). Tests can inject a custom
    callable via the constructor.
    """

    def __init__(
        self,
        search_fn: Callable[[str, int], Awaitable[list[dict[str, Any]]]] | None = None,
    ):
        self._search_fn = search_fn

    async def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        fn = self._search_fn or self._dispatch
        try:
            return await fn(query, top_k)
        except Exception:
            return []

    @staticmethod
    async def _dispatch(query: str, top_k: int) -> list[dict[str, Any]]:
        provider = (os.getenv("WEB_SEARCH_PROVIDER") or "duckduckgo").lower()
        if provider == "tavily" and os.getenv("TAVILY_API_KEY"):
            return await _tavily(query, top_k)
        return await _duckduckgo_html(query, top_k)


_HTML_RESULT = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.+?)</a>'
    r'.*?<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.+?)</a>',
    re.DOTALL,
)
_TAG = re.compile(r"<[^>]+>")


async def _duckduckgo_html(query: str, top_k: int) -> list[dict[str, Any]]:
    """Scrape DuckDuckGo's lite HTML SERP. The endpoint returns a stable
    static page (no JS) so a regex pass is enough — no Selenium, no API key.
    Returns up to `top_k` results with title/url/snippet.
    """
    import httpx

    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.5",
    }
    async with httpx.AsyncClient(
        timeout=12.0, follow_redirects=True, headers=headers
    ) as client:
        resp = await client.post(url, data={"q": query, "kl": "wt-wt"})
        if resp.status_code != 200:
            return []
        html = resp.text

    results: list[dict[str, Any]] = []
    for match in _HTML_RESULT.finditer(html):
        href = unescape(match.group("href"))
        # DDG wraps outbound links in /l/?uddg=<encoded-target>
        target = href
        parsed = urlparse(href)
        if parsed.path.startswith("/l/"):
            qs = parse_qs(parsed.query)
            redirected = qs.get("uddg", [None])[0]
            if redirected:
                target = unquote(redirected)
        title = _strip(match.group("title"))
        snippet = _strip(match.group("snippet"))
        if not title or not target:
            continue
        results.append({"title": title, "url": target, "snippet": snippet})
        if len(results) >= top_k:
            break
    return results


def _strip(html_fragment: str) -> str:
    return unescape(_TAG.sub("", html_fragment)).strip()


async def _tavily(query: str, top_k: int) -> list[dict[str, Any]]:
    import httpx

    api_key = os.getenv("TAVILY_API_KEY", "")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": top_k,
                "search_depth": "basic",
                "include_answer": False,
            },
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in (data.get("results") or [])[:top_k]
    ]


def default_web_tool() -> WebSearchTool:
    return WebSearchTool()
