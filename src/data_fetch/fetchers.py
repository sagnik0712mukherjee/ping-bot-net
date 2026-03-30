"""
fetchers.py  —  Fetch articles from all sources.

Deliberately lenient — passes anything that plausibly relates to:
  - Pritam Chakraborty (the composer)
  - His current/upcoming films: Bhooth Bangla, Cocktail 2
  - His collaborators: Arijit Singh, etc.

False positives are EXPECTED and FINE here.
The ai_filter.py module is the definitive quality gate — it runs after
fetch_all() returns and removes everything unrelated to Pritam.

Pipeline:
  1. Fetch from source
  2. Freshness check (within LOOKBACK_M_HOURS)
  3. Minimal pre-filter: at least one trigger word present anywhere in title+summary
     (very lenient — just prevents completely off-topic noise)
  4. Return raw list — ai_filter.py handles the rest
"""

import re
import logging
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

import config.settings as settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Trigger words — very broad, covers all things Pritam-adjacent
# ─────────────────────────────────────────────────────────────────────────────

# These are checked against title + summary combined.
# If ANY of these appear, the article passes pre-filter.
# Deliberately includes film/song names without "Pritam" since
# Bhooth Bangla / Cocktail 2 articles are highly likely to mention him.
_TRIGGERS = [
    "pritam",
    "bhooth bangla",
    "bhoot bangla",
    "cocktail 2",
    "tu hi disda",
    "ram ji aake",
    "arijit singh pritam",
]

# Exclusion phrases — if present, reject the article entirely
# Catches common false positives where "Pritam" appears in wrong context
_EXCLUSIONS = [
    "pritam singh",      # politician
    "pritam fc",         # footballer
    "chennaiyin fc",     # footballer
    "fire",              # unrelated news
    "arrest",            # crime news
    "drug",              # crime news
    "election",          # politics
    "voter",             # politics
    "campaign",          # politics (except movie campaigns)
    "mining",            # environmental/politics
    "elevator",          # architecture
    "family pension",     # legal news
    "fire breaks",       # accident news
    "iran",              # geopolitical
    "cricket",           # sports
    "psl",               # cricket league
    "offshore",          # oil/gas
    "cocktail recipe",   # off-topic
    "mojito",            # off-topic
]

def _is_exclusion_match(text: str) -> bool:
    """Returns True if any exclusion phrase appears in text."""
    lower = text.lower()
    for excl in _EXCLUSIONS:
        if excl in lower:
            return True
    return False

def _prefilter(text: str, title: str = "") -> bool:
    """
    Returns True if article should be included.
    - Must have at least one trigger word
    - Must NOT have any exclusion phrase
    """
    if not any(t in text.lower() for t in _TRIGGERS):
        return False
    
    # Reject if it has exclusion markers (unless "pritam" appears without the exclusion)
    # e.g., reject "Pritam Singh elected" but allow "Pritam's new song"
    combined = (title + " " + text).lower()
    
    # Special case: "pritam singh" is definitely not the composer
    if "pritam singh" in combined:
        return False
    
    # General exclusions if they appear in title or first 200 chars of text
    first_part = text[:200].lower()
    if _is_exclusion_match(first_part):
        # But allow if title explicitly mentions movie/song
        if not any(movie in title.lower() for movie in ["bhooth", "tu hi disda", "cocktail"]):
            return False
    
    return True


def _title_has_pritam(title: str) -> bool:
    """Strict check used only for Reddit and YouTube channels where
    'pritam' must be in the post title to avoid off-topic posts."""
    return "pritam" in title.lower()


# ─────────────────────────────────────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cutoff_dt(lookback_hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=lookback_hours)


def _parse_feedparser_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _dt_to_iso(dt: datetime | None) -> str:
    return dt.isoformat() if dt else ""


def _is_fresh(dt: datetime | None, lookback_hours: int) -> bool:
    if dt is None:
        return True   # unknown date → include (better to over-report)
    return dt >= _cutoff_dt(lookback_hours)


def _clean(raw: str) -> str:
    """Strip HTML, collapse whitespace, truncate."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500] + ("…" if len(text) > 500 else "")


def _strip_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", "", raw or "").strip()


def _resolve_google_alerts_url(url: str) -> str:
    """Extract real URL from Google Alerts redirect wrapper (zero HTTP)."""
    if "google.com/url" in url:
        m = re.search(r'[?&]url=([^&]+)', url)
        if m:
            from urllib.parse import unquote
            return unquote(m.group(1))
    return url


def _article(source: str, title: str, url: str,
             excerpt: str, published_at: str) -> dict:
    return {
        "source":       source,
        "title":        _strip_html(title),
        "url":          _resolve_google_alerts_url(url.strip()),
        "excerpt":      excerpt,
        "published_at": published_at,
    }


_GN_URL = (
    "https://news.google.com/rss/search"
    "?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _parse_rss(feed_url: str, source_name: str,
               lookback_hours: int,
               strict_pritam_in_title: bool = False) -> list[dict]:
    """
    Fetch RSS feed, keep entries that are fresh and pass pre-filter.
    strict_pritam_in_title=True: 'pritam' must be in title (Reddit/YT channels).
    strict_pritam_in_title=False: any trigger word in title+summary (default).
    """
    try:
        feed = feedparser.parse(
            feed_url,
            request_headers={"User-Agent": "pritam-monitor/1.0"}
        )
    except Exception as e:
        logger.warning(f"[{source_name}] RSS error: {e}")
        return []

    results = []
    for entry in feed.entries:
        dt      = _parse_feedparser_time(entry)
        title   = entry.get("title", "").strip()
        summary = entry.get("summary", "")
        if not _is_fresh(dt, lookback_hours):
            continue
        if strict_pritam_in_title:
            if not _title_has_pritam(title):
                continue
        else:
            if not _prefilter(title + " " + summary, title):
                continue
        results.append(_article(
            source       = source_name,
            title        = title,
            url          = entry.get("link", ""),
            excerpt      = _clean(summary),
            published_at = _dt_to_iso(dt),
        ))
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  TIER 1  —  Keyword-driven broad sources
# ─────────────────────────────────────────────────────────────────────────────

def fetch_newsapi(keywords: list[str], lookback_hours: int, api_key: str) -> list[dict]:
    """NewsAPI /v2/everything. Free tier: 100 req/day."""
    if not api_key or api_key == "YOUR_NEWSAPI_KEY_HERE":
        logger.info("[NewsAPI] No key — skipping.")
        return []

    results = []
    cutoff  = _cutoff_dt(lookback_hours)

    for kw in keywords:
        params = {
            "q":        kw,
            "sortBy":   "publishedAt",
            "language": "en",
            "apiKey":   api_key,
            "pageSize": 20,
        }
        try:
            resp = requests.get("https://newsapi.org/v2/everything",
                                params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"[NewsAPI] Error for '{kw}': {e}")
            continue

        for art in data.get("articles", []):
            try:
                pub_dt = datetime.fromisoformat(
                    art.get("publishedAt", "").replace("Z", "+00:00")
                )
            except Exception:
                pub_dt = None
            if pub_dt and pub_dt < cutoff:
                continue
            title = art.get("title") or ""
            if not title or title == "[Removed]":
                continue
            results.append(_article(
                source       = "NewsAPI",
                title        = title,
                url          = art.get("url", ""),
                excerpt      = _clean(art.get("description") or art.get("content") or ""),
                published_at = _dt_to_iso(pub_dt),
            ))

    logger.info(f"[NewsAPI] {len(results)} articles fetched.")
    return results


def fetch_gnews(keywords: list[str], lookback_hours: int) -> list[dict]:
    """GNews API. Free tier: 100 req/day."""
    key = getattr(settings, "GNEWS_KEY", "")
    if not key or key == "YOUR_GNEWS_KEY_HERE":
        logger.info("[GNews] No key — skipping.")
        return []

    results = []
    cutoff  = _cutoff_dt(lookback_hours)

    for kw in keywords:
        params = {"q": kw, "lang": "en", "max": 10, "apikey": key}
        try:
            resp = requests.get("https://gnews.io/api/v4/search",
                                params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"[GNews] Error for '{kw}': {e}")
            continue

        for art in data.get("articles", []):
            try:
                pub_dt = datetime.fromisoformat(
                    art.get("publishedAt", "").replace("Z", "+00:00")
                )
            except Exception:
                pub_dt = None
            if pub_dt and pub_dt < cutoff:
                continue
            title = art.get("title") or ""
            if not title:
                continue
            results.append(_article(
                source       = "GNews",
                title        = title,
                url          = art.get("url", ""),
                excerpt      = _clean(art.get("description") or ""),
                published_at = _dt_to_iso(pub_dt),
            ))

    logger.info(f"[GNews] {len(results)} articles fetched.")
    return results


def fetch_google_alerts(feed_urls: list[str], lookback_hours: int) -> list[dict]:
    """
    Google Alerts RSS feeds — no key needed.
    Lenient: passes everything fresh. AI filter will handle noise.
    (Google Alerts can produce junk titles that don't match the article content —
    we pass all of them and let GPT-4.1 sort it out.)
    """
    if not feed_urls:
        logger.info("[Google Alerts] No URLs — skipping.")
        return []

    results = []
    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logger.warning(f"[Google Alerts] Error: {e}")
            continue
        for entry in feed.entries:
            dt      = _parse_feedparser_time(entry)
            title   = _strip_html(entry.get("title", ""))
            summary = _clean(entry.get("summary", ""))
            if not _is_fresh(dt, lookback_hours):
                continue
            # Only minimal pre-filter: skip if completely empty
            if not title and not summary:
                continue
            results.append(_article(
                source       = "Google Alerts",
                title        = title,
                url          = entry.get("link", ""),
                excerpt      = summary,
                published_at = _dt_to_iso(dt),
            ))

    logger.info(f"[Google Alerts] {len(results)} articles fetched.")
    return results


def fetch_reddit(subreddits: list[str], keywords: list[str],
                 lookback_hours: int) -> list[dict]:
    """Reddit subreddit RSS search. 'pritam' must be in post title."""
    results = []
    headers = {"User-Agent": "pritam-monitor/1.0"}

    for sub in subreddits:
        for kw in keywords:
            url = (f"https://www.reddit.com/r/{sub}/search.rss"
                   f"?q={quote_plus(kw)}&sort=new&restrict_sr=on")
            try:
                feed = feedparser.parse(url, request_headers=headers)
            except Exception as e:
                logger.warning(f"[Reddit] r/{sub} '{kw}': {e}")
                continue
            for entry in feed.entries:
                dt    = _parse_feedparser_time(entry)
                title = entry.get("title", "").strip()
                if not _is_fresh(dt, lookback_hours):
                    continue
                if not _title_has_pritam(title):
                    continue
                results.append(_article(
                    source       = f"Reddit r/{sub}",
                    title        = title,
                    url          = entry.get("link", ""),
                    excerpt      = _clean(entry.get("summary", "")),
                    published_at = _dt_to_iso(dt),
                ))

    logger.info(f"[Reddit] {len(results)} posts fetched.")
    return results


_PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.adminforge.de",
    "https://api.piped.projectsegfau.lt",
]

def fetch_youtube_search(keywords: list[str], lookback_hours: int) -> list[dict]:
    """YouTube search via Piped API, falls back to Google News site:youtube.com."""
    cutoff  = _cutoff_dt(lookback_hours)
    results = []

    for kw in keywords:
        fetched = False
        for instance in _PIPED_INSTANCES:
            try:
                resp = requests.get(
                    f"{instance}/search?q={quote_plus(kw)}&filter=videos",
                    timeout=15
                )
                resp.raise_for_status()
                for v in resp.json().get("items", []):
                    if v.get("type") != "stream":
                        continue
                    uploaded_ms = v.get("uploaded")
                    pub_dt = (datetime.fromtimestamp(uploaded_ms / 1000, tz=timezone.utc)
                              if uploaded_ms else None)
                    if pub_dt and pub_dt < cutoff:
                        continue
                    title = v.get("title", "").strip()
                    if not title:
                        continue
                    video_id = v.get("url", "").lstrip("/watch?v=").split("&")[0]
                    results.append(_article(
                        source       = "YouTube",
                        title        = title,
                        url          = f"https://www.youtube.com/watch?v={video_id}",
                        excerpt      = _clean(v.get("shortDescription", "")),
                        published_at = _dt_to_iso(pub_dt),
                    ))
                fetched = True
                break
            except Exception as e:
                logger.warning(f"[YouTube/Piped] {instance} failed for '{kw}': {e}")
                continue

        if not fetched:
            # Fallback: Google News scoped to youtube.com
            feed = feedparser.parse(
                _GN_URL.format(query=quote_plus(f"{kw} site:youtube.com"))
            )
            for entry in feed.entries:
                dt    = _parse_feedparser_time(entry)
                title = entry.get("title", "").strip()
                if not _is_fresh(dt, lookback_hours):
                    continue
                summary = entry.get("summary", "")
                if not _prefilter(title + " " + summary, title):
                    continue
                results.append(_article(
                    source       = "YouTube",
                    title        = title,
                    url          = entry.get("link", ""),
                    excerpt      = _clean(summary),
                    published_at = _dt_to_iso(dt),
                ))

    logger.info(f"[YouTube Search] {len(results)} videos fetched.")
    return results


def fetch_youtube_channels(channel_ids: list[str], lookback_hours: int) -> list[dict]:
    """YouTube channel RSS — 'pritam' must appear in video title."""
    results = []
    for channel_id in channel_ids:
        try:
            feed = feedparser.parse(
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            )
        except Exception as e:
            logger.warning(f"[YouTube Channels] {channel_id}: {e}")
            continue
        for entry in feed.entries:
            dt    = _parse_feedparser_time(entry)
            title = entry.get("title", "").strip()
            if not _is_fresh(dt, lookback_hours):
                continue
            if not _title_has_pritam(title):
                continue
            results.append(_article(
                source       = "YouTube (channel)",
                title        = title,
                url          = entry.get("link", ""),
                excerpt      = _clean(entry.get("summary", "")),
                published_at = _dt_to_iso(dt),
            ))

    logger.info(f"[YouTube Channels] {len(results)} videos fetched.")
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  TIER 2  —  Direct named-outlet scrapers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_site_scoped(site_domain: str, source_name: str) -> list[dict]:
    """
    Google News search scoped to a domain, one query per keyword.
    Deduplicates results internally. Uses improved pre-filter to reduce trash.
    """
    results   = []
    seen_urls: set[str] = set()

    for kw in settings.KEYWORDS:
        query = f"{kw} site:{site_domain}"
        feed  = feedparser.parse(_GN_URL.format(query=quote_plus(query)))
        for entry in feed.entries:
            dt    = _parse_feedparser_time(entry)
            url   = entry.get("link", "")
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "")
            if not _is_fresh(dt, settings.LOOKBACK_M_HOURS):
                continue
            if url in seen_urls:
                continue
            # Apply pre-filter to reduce trash (e.g., fire news, crime, politics with "Pritam Singh")
            if not _prefilter(title + " " + summary, title):
                continue
            seen_urls.add(url)
            results.append(_article(
                source       = source_name,
                title        = title,
                url          = url,
                excerpt      = _clean(summary),
                published_at = _dt_to_iso(dt),
            ))
    return results


def fetch_toi() -> list[dict]:
    results = []
    # Direct RSS feeds
    for feed_url in [
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
    ]:
        results.extend(_parse_rss(feed_url, "Times of India", settings.LOOKBACK_M_HOURS))
    # Also Google News site-scoped
    results.extend(_fetch_site_scoped("timesofindia.indiatimes.com", "Times of India"))
    logger.info(f"[TOI] {len(results)} articles.")
    return results


def fetch_filmfare() -> list[dict]:
    results = _fetch_site_scoped("filmfare.com", "Filmfare")
    results.extend(_parse_rss(
        "https://www.filmfare.com/feeds/feeds.xml",
        "Filmfare", settings.LOOKBACK_M_HOURS
    ))
    logger.info(f"[Filmfare] {len(results)} articles.")
    return results


def fetch_zoom() -> list[dict]:
    results = _fetch_site_scoped("zoomtventertainment.com", "Zoom TV Entertainment")
    results.extend(_parse_rss(
        "https://www.zoomtventertainment.com/feeds/bollywood.xml",
        "Zoom TV Entertainment", settings.LOOKBACK_M_HOURS
    ))
    logger.info(f"[Zoom TV] {len(results)} articles.")
    return results


def fetch_pinkvilla() -> list[dict]:
    r = _parse_rss("https://www.pinkvilla.com/feed", "Pinkvilla", settings.LOOKBACK_M_HOURS)
    logger.info(f"[Pinkvilla] {len(r)} articles.")
    return r


def fetch_bollywood_hungama() -> list[dict]:
    r = _parse_rss("https://www.bollywoodhungama.com/feed/",
                   "Bollywood Hungama", settings.LOOKBACK_M_HOURS)
    logger.info(f"[Bollywood Hungama] {len(r)} articles.")
    return r


def fetch_ndtv() -> list[dict]:
    r = _parse_rss("https://feeds.feedburner.com/NdtvEntertainment",
                   "NDTV Entertainment", settings.LOOKBACK_M_HOURS)
    logger.info(f"[NDTV] {len(r)} articles.")
    return r


def fetch_imdb() -> list[dict]:
    """Scrapes Pritam's IMDB news page. Falls back to Google News site-scoped."""
    headers = {"User-Agent": _BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"}
    try:
        resp = requests.get("https://www.imdb.com/name/nm0679665/news",
                            headers=headers, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.warning(f"[IMDB] Page fetch failed: {e} — using fallback")
        return _imdb_fallback()

    results = []
    seen    = set()
    for path, raw_title in re.findall(
        r'href="(/news/ni\d+[^"]*)"[^>]*>\s*<[^>]+>\s*(.*?)\s*</[^>]+>',
        html, re.DOTALL
    ):
        title = _clean(raw_title)
        if not title or path in seen:
            continue
        seen.add(path)
        results.append(_article(
            source="IMDB", title=title,
            url="https://www.imdb.com" + path,
            excerpt="", published_at="",
        ))

    logger.info(f"[IMDB] {len(results)} items (page scrape).")
    return results if results else _imdb_fallback()


def _imdb_fallback() -> list[dict]:
    results = []
    for kw in settings.KEYWORDS[:3]:
        feed = feedparser.parse(
            _GN_URL.format(query=quote_plus(f"{kw} site:imdb.com/news"))
        )
        for entry in feed.entries:
            dt = _parse_feedparser_time(entry)
            if not _is_fresh(dt, settings.LOOKBACK_M_HOURS):
                continue
            results.append(_article(
                source="IMDB",
                title=entry.get("title", "").strip(),
                url=entry.get("link", ""),
                excerpt=_clean(entry.get("summary", "")),
                published_at=_dt_to_iso(dt),
            ))
    logger.info(f"[IMDB] {len(results)} items (fallback).")
    return results


_INSTAGRAM_MIRRORS = [
    ("imginn",  "https://imginn.com/pritamofficial/"),
    ("imgsed",  "https://imgsed.com/pritamofficial/"),
    ("inflact", "https://inflact.com/profiles/instagram/pritamofficial/"),
]

def fetch_instagram() -> list[dict]:
    cutoff  = _cutoff_dt(settings.LOOKBACK_M_HOURS)
    headers = {"User-Agent": _BROWSER_UA}

    for mirror_name, mirror_url in _INSTAGRAM_MIRRORS:
        try:
            resp = requests.get(mirror_url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.warning(f"[Instagram/{mirror_name}] {e}")
            continue

        results    = []
        seen_codes = set()
        post_links = re.findall(
            r'href="(https?://(?:www\.)?(?:instagram\.com|imginn\.com|imgsed\.com)'
            r'/(?:p|pritamofficial/p)/([A-Za-z0-9_-]+)/?)"', html
        )
        time_tags = re.findall(r'<time[^>]+datetime="([^"]+)"', html)

        for full_url, shortcode in post_links:
            if shortcode in seen_codes:
                continue
            seen_codes.add(shortcode)
            idx     = html.find(shortcode)
            snippet = html[max(0, idx-200):idx+500] if idx != -1 else ""
            caption = _clean(re.sub(r"<[^>]+>", " ", snippet))[:200]
            pub_dt  = None
            if time_tags:
                try:
                    pub_dt = datetime.fromisoformat(time_tags[0].replace("Z", "+00:00"))
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
            results.append(_article(
                source       = "Instagram (@pritamofficial)",
                title        = caption[:100] or "New post by Pritam",
                url          = f"https://www.instagram.com/p/{shortcode}/",
                excerpt      = caption,
                published_at = _dt_to_iso(pub_dt),
            ))

        if results:
            logger.info(f"[Instagram/{mirror_name}] {len(results)} posts.")
            return results
        logger.warning(f"[Instagram/{mirror_name}] No posts found.")

    logger.warning("[Instagram] All mirrors failed.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
#  Master fetch — called by main.py
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    """
    Runs all enabled sources and returns a deduplicated list.
    NOTE: This does NOT run AI filtering — that happens in main.py
    via ai_filter.apply_filter() AFTER dedup.
    """
    raw: list[dict] = []

    if settings.ENABLE_NEWSAPI:
        raw.extend(fetch_newsapi(settings.KEYWORDS, settings.LOOKBACK_M_HOURS, settings.NEWSAPI_KEY))
    if settings.ENABLE_GNEWS:
        raw.extend(fetch_gnews(settings.KEYWORDS, settings.LOOKBACK_M_HOURS))
    if settings.ENABLE_GOOGLE_ALERTS_RSS:
        raw.extend(fetch_google_alerts(settings.GOOGLE_ALERTS_RSS_URLS, settings.LOOKBACK_M_HOURS))
    if settings.ENABLE_REDDIT:
        raw.extend(fetch_reddit(settings.REDDIT_SUBREDDITS, settings.KEYWORDS, settings.LOOKBACK_M_HOURS))
    if settings.ENABLE_YOUTUBE:
        raw.extend(fetch_youtube_search(settings.KEYWORDS, settings.LOOKBACK_M_HOURS))
        raw.extend(fetch_youtube_channels(settings.YOUTUBE_CHANNEL_IDS, settings.LOOKBACK_M_HOURS))
    if settings.ENABLE_TOI:
        raw.extend(fetch_toi())
    if settings.ENABLE_FILMFARE:
        raw.extend(fetch_filmfare())
    if settings.ENABLE_ZOOM:
        raw.extend(fetch_zoom())
    if settings.ENABLE_PINKVILLA:
        raw.extend(fetch_pinkvilla())
    if settings.ENABLE_BOLLYWOOD_HUNGAMA:
        raw.extend(fetch_bollywood_hungama())
    if settings.ENABLE_NDTV:
        raw.extend(fetch_ndtv())
    if settings.ENABLE_IMDB:
        raw.extend(fetch_imdb())
    if settings.ENABLE_INSTAGRAM:
        raw.extend(fetch_instagram())

    # Deduplicate by URL
    seen:    set[str]   = set()
    deduped: list[dict] = []
    for item in raw:
        url = item.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(item)

    logger.info(f"[fetch_all] {len(raw)} raw → {len(deduped)} unique articles.")
    return deduped
