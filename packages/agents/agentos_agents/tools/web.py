from __future__ import annotations

import asyncio
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

    When `WEB_SEARCH_IMAGES=true` (default) we additionally fetch each top
    result's HTML and extract `<meta property="og:image">` so the chat
    bubble can render thumbnails for context. This is bounded by a strict
    per-URL timeout and runs in parallel — total latency overhead is
    typically the slowest single fetch.

    Set `WEB_SEARCH_PROVIDER=tavily` plus `TAVILY_API_KEY` to upgrade to
    Tavily (better recall + native image_url support, requires signup).
    Tests can inject a custom callable via the constructor.
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
        results = await _duckduckgo_html(query, top_k)
        if results and _images_enabled():
            await _enrich_with_og_images(results)
        return results


_HTML_RESULT = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.+?)</a>'
    r'.*?<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.+?)</a>',
    re.DOTALL,
)
# DuckDuckGo HTML SERP wraps sponsored slots in `result result--ad` blocks
# alongside organic `result results_links` blocks. Strip ad blocks before
# regex extraction so eBay / ticket vendors / shopping ads don't pollute
# the source list. Match the opening div + everything until the next
# closing </div> at the same nesting level — DDG's ad blocks are flat so
# a non-greedy match works.
_AD_BLOCK = re.compile(
    r'<div[^>]+class="[^"]*result--ad[^"]*"[^>]*>.*?<div\s+class="clear"></div>',
    re.DOTALL | re.IGNORECASE,
)
# Domains that consistently pollute SERPs with shopping / ticket ads
# regardless of the query topic. Filtered after parsing as a backstop.
_SPAM_HOSTS = (
    "ebay.com",
    "ebay.es",
    "amazon.com",
    "amazon.es",
    "amazon.co.uk",
    "vividseats.com",
    "stubhub.com",
    "seatgeek.com",
    "ticketmaster.com",
    "viagogo.com",
    "expedia.com",
    "booking.com",
)
# Title patterns that scream "this is an ad, not informational content".
_SPAM_TITLE = re.compile(
    r"(?:Official Site\s*[-—|]|Buy Now|Last[- ]Minute Tickets|Fantastic Prices|"
    r"Lowest Prices|Shop On |Compra productos únicos|Descubre grandes ofertas)",
    re.IGNORECASE,
)
# Queries that reference "current", "right now", "this season/year/month/week"
# get scoped to DuckDuckGo's past-year window via `df=y`. We don't trigger on
# bare year numbers alone — the user might ask about 2023 historically — but
# explicit "actual" / "reciente" / "current" / "now" / "este año" is unambiguous.
_TIME_SENSITIVE = re.compile(
    r"\b("
    r"actual(?:es|mente)?|reciente(?:s|mente)?|hoy|ahora|"
    r"este\s+(?:año|mes|semana|temporada)|esta\s+(?:semana|temporada)|"
    r"current(?:ly)?|recent(?:ly)?|today|now|latest|"
    r"this\s+(?:year|month|week|season)|"
    r"who\s+is\s+winning|going\s+on\s+now"
    r")\b",
    re.IGNORECASE,
)
_TAG = re.compile(r"<[^>]+>")
_OG_IMAGE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_TWITTER_IMAGE = re.compile(
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _images_enabled() -> bool:
    return os.getenv("WEB_SEARCH_IMAGES", "true").lower() not in ("false", "0", "no")


async def _duckduckgo_html(query: str, top_k: int) -> list[dict[str, Any]]:
    """Scrape DuckDuckGo's lite HTML SERP. The endpoint returns a stable
    static page (no JS) so a regex pass is enough — no Selenium, no API key.
    Returns up to `top_k` filtered results with title/url/snippet.

    Filtering pipeline (in order):
      1. Strip the entire `result--ad` block from the HTML before parsing —
         removes sponsored slots that DDG injects into the SERP regardless
         of relevance (eBay, Amazon, ticket vendors etc.).
      2. After regex extraction, drop any result whose host matches a
         known shopping/ticket spam domain (_SPAM_HOSTS) — backstop in
         case an ad slipped past step 1 without the result--ad class.
      3. Drop results whose title matches the ad-copy patterns
         (`_SPAM_TITLE`: "Buy Now", "Official Site -", "Last-Minute
         Tickets", etc.).
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
        # Pass `kl=wt-wt` (no region bias). When the query looks
        # time-sensitive ("current Champions semis", "este año") add
        # `df=y` so DDG scopes to the past 12 months — old recap pages
        # were drowning recent news in the SERP for these queries.
        form = {"q": query, "kl": "wt-wt"}
        if _TIME_SENSITIVE.search(query):
            form["df"] = "y"
        resp = await client.post(url, data=form)
        if resp.status_code != 200:
            return []
        html = resp.text

    # Step 1 — strip ad blocks at the HTML level.
    html = _AD_BLOCK.sub("", html)

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
        # Step 2 — drop results whose host is on the spam list.
        host = urlparse(target).hostname or ""
        host_norm = host.lower().lstrip("www.")
        if any(host_norm == s or host_norm.endswith("." + s) for s in _SPAM_HOSTS):
            continue
        # Step 3 — drop results with ad-copy titles.
        if _SPAM_TITLE.search(title):
            continue
        results.append({"title": title, "url": target, "snippet": snippet, "image": None})
        if len(results) >= top_k:
            break
    return results


async def _enrich_with_og_images(results: list[dict[str, Any]]) -> None:
    """Fetch og:image / twitter:image from each result URL in parallel.

    Strict per-URL timeout (5s) so a slow page can't drag the whole search
    down. Failures are silent — the result simply keeps `image=None` and
    the UI renders without a thumbnail.
    """
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    async def fetch_image(client: httpx.AsyncClient, item: dict) -> None:
        url = item.get("url")
        if not url:
            return
        try:
            r = await client.get(url, headers=headers, timeout=5.0)
            if r.status_code != 200:
                return
            # Only scan the first 64 KB — og tags live in <head>.
            head = r.text[:65_536]
        except Exception:
            return
        m = _OG_IMAGE.search(head) or _TWITTER_IMAGE.search(head)
        if m:
            img = unescape(m.group(1))
            # Resolve relative URLs against the result's host.
            if img.startswith("//"):
                img = "https:" + img
            elif img.startswith("/"):
                parsed = urlparse(url)
                img = f"{parsed.scheme}://{parsed.netloc}{img}"
            item["image"] = img

    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch_image(client, r) for r in results))


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
                "include_images": True,
            },
        )
        if resp.status_code != 200:
            return []
        data = resp.json()

    images = data.get("images") or []
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
            "image": images[i] if i < len(images) and isinstance(images[i], str) else None,
        }
        for i, r in enumerate((data.get("results") or [])[:top_k])
    ]


def default_web_tool() -> WebSearchTool:
    return WebSearchTool()
