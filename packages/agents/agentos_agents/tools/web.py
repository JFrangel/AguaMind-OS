from __future__ import annotations

import asyncio
import datetime
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
            results = await _tavily(query, top_k)
        else:
            results = await _duckduckgo_html(query, top_k)
            if results:
                # Single fetch per URL extracts og:image, main article body,
                # AND publication date in one pass. The body unblocks the
                # writer when DDG snippets are too short; the date lets us
                # rank time-sensitive queries newest-first so a speculative
                # article from before the event doesn't dominate fresh news.
                await _enrich_results(results, with_images=_images_enabled())

        if not results:
            return results
        is_time_sensitive = bool(_TIME_SENSITIVE.search(query))

        # PREFER body items but don't drop the rest. Reorder so items
        # with a fetched body come first (richer context for the writer),
        # and items with only a SERP snippet come after. This keeps the
        # source count high while pushing the empty/timed-out items
        # (UEFA, JS-heavy sites) to the bottom of the writer's context
        # rather than to its top. The number of total results stays the
        # same as what DDG returned.
        body_items = [r for r in results if (r.get("body") or "").strip()]
        snippet_only = [r for r in results if not (r.get("body") or "").strip()]
        results = body_items + snippet_only

        # For time-sensitive queries (semifinales, cuartos, "este año"),
        # drop articles older than 180 days — likely from a previous
        # season / cycle. Items WITHOUT a date are kept (lack of date
        # is uninformative). Falls back to the un-filtered list if
        # filtering would leave us empty.
        if is_time_sensitive:
            cutoff = (datetime.date.today() - datetime.timedelta(days=180)).isoformat()
            filtered = [r for r in results if (r.get("published") or "9999") >= cutoff]
            if filtered:
                results = filtered

        # Compute authority + recency scores then sort by:
        #   (authority desc, recency desc when time-sensitive, original idx)
        # SBERT → sbert.net + huggingface.co first; Champions semis →
        # uefa.com first, then most recent news; .gov queries → agency
        # above blogs. Stable sort preserves DDG ranking on ties.
        for item in results:
            host = (urlparse(item.get("url") or "").hostname or "").lower()
            item["_authority"] = _authority_score(host)
        results.sort(
            key=lambda r: (
                -r.get("_authority", 0),
                _negative_date_key(r.get("published") or "") if is_time_sensitive else 0,
            )
        )
        for item in results:
            item.pop("_authority", None)
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
# Authoritative / official domains that get a ranking boost. Two tiers:
# tier 2 (highest) for primary sources (the org itself, governments,
# academic), tier 1 for community-authoritative (Wikipedia, MDN,
# StackOverflow), 0 for everyone else. Within the same tier we fall
# back to recency (for time-sensitive queries) or SERP order. A user
# asking about SBERT gets sbert.net first; about Champions League gets
# uefa.com first; about "covid CDC guidelines" gets cdc.gov first.
_AUTHORITY_TIER_2: tuple[str, ...] = (
    # Sports / orgs
    "uefa.com", "fifa.com", "olympic.org", "olympics.com", "nba.com",
    "nfl.com", "mlb.com", "atptour.com", "wtatennis.com",
    # Tech: official docs / project sites
    "python.org", "docs.python.org", "nodejs.org", "react.dev",
    "vuejs.org", "svelte.dev", "angular.dev", "kotlinlang.org",
    "go.dev", "rust-lang.org", "ruby-lang.org", "kernel.org",
    "developer.mozilla.org", "w3.org", "whatwg.org", "ietf.org",
    "rfc-editor.org", "ecma-international.org", "tc39.es",
    "sbert.net", "huggingface.co", "pytorch.org", "tensorflow.org",
    "scikit-learn.org", "numpy.org", "scipy.org", "pandas.pydata.org",
    "fastapi.tiangolo.com", "djangoproject.com", "flask.palletsprojects.com",
    "pypi.org", "npmjs.com", "rubygems.org", "crates.io",
    "kubernetes.io", "docker.com", "helm.sh", "terraform.io",
    "supabase.com", "vercel.com", "cloudflare.com", "anthropic.com",
    "openai.com", "platform.openai.com", "ai.google.dev",
    # Science / medical / institutional
    "nih.gov", "cdc.gov", "fda.gov", "who.int", "europa.eu",
    "nature.com", "science.org", "arxiv.org", "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov", "mit.edu", "stanford.edu", "cmu.edu",
)
_AUTHORITY_TIER_1: tuple[str, ...] = (
    # Community-authoritative
    "wikipedia.org", "stackoverflow.com", "github.com",
    "reuters.com", "bbc.com", "apnews.com",
)
# Suffix-based authority — anything ending with these gets tier 2 by
# default (governments and accredited universities).
_AUTHORITY_SUFFIXES: tuple[str, ...] = (".gov", ".edu", ".gob.es", ".gob.mx")


def _negative_date_key(published: str) -> str:
    """Sort key that puts the NEWEST date first when used with ascending sort.

    Trick: lexicographic comparison of YYYY-MM-DD strings is the same as
    chronological. To put newest first under ascending sort we'd negate,
    but strings can't be negated, so we map "2026-04-30" → a string that
    sorts EARLIER for newer dates. We use Unicode codepoint inversion via
    chr(0x10FFFF - ord(c)) — but a far simpler approach is to just put
    the date string into a tuple `(no_date_flag, -date_int)`. For
    simplicity here, we return ISO and let Python compare lexicographically
    AFTER inversion: build a string where each digit is replaced by its
    9's-complement, so "2026" → "7973" and newer dates get smaller strings.
    """
    if not published:
        # Items without a date go last among the same authority tier.
        return "￿"  # sorts after any real date string
    out = []
    for ch in published:
        if ch.isdigit():
            out.append(str(9 - int(ch)))
        else:
            out.append(ch)
    return "".join(out)


def _authority_score(host: str) -> int:
    h = host.lower().lstrip(".").removeprefix("www.")
    for d in _AUTHORITY_TIER_2:
        if h == d or h.endswith("." + d):
            return 2
    for d in _AUTHORITY_TIER_1:
        if h == d or h.endswith("." + d):
            return 1
    if any(h.endswith(s) for s in _AUTHORITY_SUFFIXES):
        return 2
    # Patterns: docs.* / developer.* / api.* / spec.* are usually
    # primary technical sources.
    if h.startswith(("docs.", "developer.", "developers.", "api.", "spec.")):
        return 1
    return 0


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
# OR a competition-stage word (semifinal, cuartos, jornada, ranking) get
# scoped to DuckDuckGo's past-year window via `df=y` AND old articles
# (>180 days) get filtered out. Stage words imply "current state of the
# competition" by definition — nobody asks "who's in the semifinal"
# meaning historically. We don't trigger on bare year numbers alone —
# the user might ask about 2023 historically.
_TIME_SENSITIVE = re.compile(
    r"\b("
    # Explicit recency markers
    r"actual(?:es|mente)?|reciente(?:s|mente)?|hoy|ahora|"
    r"este\s+(?:año|mes|semana|temporada)|esta\s+(?:semana|temporada)|"
    r"current(?:ly)?|recent(?:ly)?|today|now|latest|"
    r"this\s+(?:year|month|week|season)|"
    r"who\s+is\s+winning|going\s+on\s+now|"
    # Competition-stage / event-state vocabulary (implicitly current)
    r"semifinal(?:es)?|cuartos|octavos|dieciseisavos|"
    r"jornada|fixture|ranking|standings|clasificaci[oó]n|"
    # "están|estan + clasificados|en liza|en la final"
    r"est[áa]n?\s+(?:clasificad|en\s+liza|en\s+la\s+final|en\s+semis?)"
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
# Article publication date. Most modern sites expose at least one of
# these. We try them in order and pick the first hit. The format varies
# (ISO 8601 with or without timezone) — we just normalize to YYYY-MM-DD
# for sorting and display.
_PUBLISHED_PATTERNS = (
    re.compile(
        r'<meta[^>]+(?:property|name|itemprop)=["\'](?:article:published_time|og:published_time|article:modified_time|pubdate|datePublished|date)["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\'](?:article:published_time|og:published_time|datePublished)["\']',
        re.IGNORECASE,
    ),
    re.compile(r'<time[^>]+datetime=["\']([^"\']+)["\']', re.IGNORECASE),
)
_DATE_ISO = re.compile(r"(\d{4}-\d{2}-\d{2})")
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
            # 8s is a compromise: enough for JS-heavy authoritative sites
            # (UEFA, large news outlets) that take a few seconds to serve
            # their first byte, but capped so a hung server can't drag
            # down the whole search. asyncio.gather still parallelizes
            # across results, so total latency is the slowest single hit.
            r = await client.get(url, headers=headers, timeout=8.0)
            if r.status_code != 200:
                return
            full = r.text
        except Exception:
            return

        # Head metadata lives in the first 64 KB; scan that slice once.
        head = full[:65_536]

        if with_images:
            m = _OG_IMAGE.search(head) or _TWITTER_IMAGE.search(head)
            if m:
                img = unescape(m.group(1))
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    parsed = urlparse(url)
                    img = f"{parsed.scheme}://{parsed.netloc}{img}"
                item["image"] = img

        # Publication date: try several meta tag forms in order, fall
        # back to the first <time datetime="..."> in the body. We
        # normalize to YYYY-MM-DD for both display and sortability.
        for pattern in _PUBLISHED_PATTERNS:
            dm = pattern.search(head)
            if dm:
                raw = unescape(dm.group(1))
                iso = _DATE_ISO.search(raw)
                if iso:
                    item["published"] = iso.group(1)
                    break

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
