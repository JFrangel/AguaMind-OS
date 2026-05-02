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
        if results:
            # Single fetch per URL extracts og:image + main article body
            # in one pass. The body text is what unblocks the writer when
            # DDG's snippet is too short to contain the actual answer
            # (team names, prices, etc.).
            await _enrich_results(results, with_images=_images_enabled())
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
# Queries that explicitly want shopping/commercial results. When a user
# asks "compara precios de iPhone en eBay" we MUST keep shopping domains
# in the SERP — the spam filter is the wrong default for those. Detected
# via intent words; if any match, we skip both the host blocklist and
# the title blocklist.
_COMMERCIAL_INTENT = re.compile(
    r"\b("
    r"comprar|precio|precios|barato|barata|baratos|baratas|oferta|ofertas|"
    r"venta|ventas|vender|tienda|tiendas|amazon|ebay|"
    r"comparar\s+precio|donde\s+comprar|cu[áa]nto\s+(?:cuesta|vale)|"
    r"price|prices|cheap|deal|deals|buy|where\s+to\s+buy|shopping|"
    r"how\s+much\s+(?:does|is)|coupon|discount"
    r")\b",
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
# Article body extractors. Try <article>, then <main>, then <body>. Each
# is non-greedy and case-insensitive — most modern news sites wrap their
# main content in <article>. Score depends on which page we hit, but at
# minimum <body> always exists.
_ARTICLE_TAG = re.compile(r"<article\b[^>]*>([\s\S]*?)</article>", re.IGNORECASE)
_MAIN_TAG = re.compile(r"<main\b[^>]*>([\s\S]*?)</main>", re.IGNORECASE)
_BODY_TAG = re.compile(r"<body\b[^>]*>([\s\S]*?)</body>", re.IGNORECASE)
# Tags whose content is NOT article body: scripts, styles, navs, headers,
# footers, sidebars, forms, ads. Strip these wholesale before we extract
# the visible text — otherwise the writer sees megabytes of menu items
# and JS libs.
_NOISE_TAG = re.compile(
    r"<(?:script|style|nav|header|footer|aside|form|noscript|svg|iframe)\b[^>]*>"
    r"[\s\S]*?</(?:script|style|nav|header|footer|aside|form|noscript|svg|iframe)>",
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

    # Spam filtering is conditional on intent. For informational queries
    # ("quien va a ganar la champions"), eBay/ticket-vendor results are
    # noise. For shopping queries ("comparar precios de iPhone en eBay"),
    # those same domains ARE the answer — never block them.
    is_shopping = bool(_COMMERCIAL_INTENT.search(query))

    # Step 1 — strip ad blocks at the HTML level (only for non-shopping).
    if not is_shopping:
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
        if not is_shopping:
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


async def _enrich_results(
    results: list[dict[str, Any]],
    *,
    with_images: bool = True,
    body_max_chars: int = 1500,
) -> None:
    """Fetch each result's HTML and extract og:image + main article body
    text in one pass. Without this, the writer only sees DDG's ~150-char
    snippets which often end with "..." and don't contain the actual
    answer (team names, prices, dates, etc.).

    Strict per-URL timeout (5s) so a slow page can't drag the whole search
    down. Failures are silent — the result keeps `image=None` and `body=""`
    and the writer falls back to the snippet.
    """
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    async def fetch_one(client: httpx.AsyncClient, item: dict) -> None:
        url = item.get("url")
        if not url:
            return
        try:
            r = await client.get(url, headers=headers, timeout=5.0)
            if r.status_code != 200:
                return
            full = r.text
        except Exception:
            return

        if with_images:
            # og tags live in <head>, scan only the first 64 KB.
            m = _OG_IMAGE.search(full[:65_536]) or _TWITTER_IMAGE.search(full[:65_536])
            if m:
                img = unescape(m.group(1))
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    parsed = urlparse(url)
                    img = f"{parsed.scheme}://{parsed.netloc}{img}"
                item["image"] = img

        # Article body extraction: prefer <article>/<main>, else <body>.
        # Strip noise tags (script/style/nav/header/footer/aside/form).
        # Then strip remaining HTML tags, normalize whitespace, truncate.
        body_match = (
            _ARTICLE_TAG.search(full)
            or _MAIN_TAG.search(full)
            or _BODY_TAG.search(full)
        )
        if body_match:
            chunk = body_match.group(1)
            chunk = _NOISE_TAG.sub(" ", chunk)
            chunk = _TAG.sub(" ", chunk)
            chunk = unescape(chunk)
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if chunk:
                item["body"] = chunk[:body_max_chars]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch_one(client, r) for r in results))


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
    # Tavily's `content` field is already the article-extract, much
    # richer than DDG's snippet. We expose it as both `snippet` (back-
    # compat) and `body` (so the writer-side block uses the longer text
    # via the same code path as DDG enrichment).
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
            "body": r.get("content", ""),
            "image": images[i] if i < len(images) and isinstance(images[i], str) else None,
        }
        for i, r in enumerate((data.get("results") or [])[:top_k])
    ]


def default_web_tool() -> WebSearchTool:
    return WebSearchTool()
