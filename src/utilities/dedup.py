# ═══════════════════════════════════════════════════════════════
#  dedup.py  —  Persistent deduplication across runs
#
#  Uses a JSON file (seen_urls.json) to track every URL that has
#  ever been emailed. Delete the file to reset and start fresh.
#
#  Key design: ALL dedup (batch + persistent) works on a
#  *normalised* URL so the same article fetched via RSS and via
#  Google News gets an identical hash and is deduplicated.
# ═══════════════════════════════════════════════════════════════

import json
import hashlib
import os
import re
import logging
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

logger = logging.getLogger(__name__)


# ── Params that differ across sources for the same article ─────
# These are stripped before hashing so two URLs pointing at the
# same article get the same fingerprint.
_JUNK_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_content",
    "utm_term", "usp", "ved", "ei", "hl", "gl", "ceid",
    "source", "ref", "referer", "fbclid", "gclid",
    "_ga", "_gl", "mc_cid", "mc_eid",
}


def _normalise_url(url: str) -> str:
    """
    Normalise a URL for fingerprinting:
    1. Strip Google redirect wrappers  (google.com/url?...&url=TARGET)
    2. Lowercase scheme + host
    3. Remove trailing slash from path
    4. Drop tracking / noise query params
    5. Sort remaining params for consistency
    """
    url = url.strip()

    # 1. Unwrap Google redirect  (?url=...  or  &url=...)
    if "google.com/url" in url:
        m = re.search(r'[?&]url=([^&]+)', url)
        if m:
            from urllib.parse import unquote
            url = unquote(m.group(1))

    # Also handle Google News /rss/articles/ redirects
    if "news.google.com/rss/articles" in url:
        m = re.search(r'[?&]url=([^&]+)', url)
        if m:
            from urllib.parse import unquote
            url = unquote(m.group(1))

    try:
        parsed = urlparse(url)
        # 2. Lowercase scheme + host
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower().lstrip("www.")  # treat www. as optional
        # 3. Remove trailing slash
        path = parsed.path.rstrip("/")
        # 4. Drop junk params, keep the rest sorted
        qs = parse_qs(parsed.query, keep_blank_values=False)
        clean_qs = {k: v for k, v in qs.items() if k.lower() not in _JUNK_PARAMS}
        # 5. Reconstruct — no fragment
        clean_query = urlencode(
            sorted((k, v[0]) for k, v in clean_qs.items())
        )
        normalised = urlunparse((scheme, netloc, path, "", clean_query, ""))
        return normalised.lower()
    except Exception:
        return url.lower()


def _hash(url: str) -> str:
    """MD5 hash of a *normalised* URL — used as the stored key."""
    return hashlib.md5(_normalise_url(url).encode()).hexdigest()


def _title_hash(title: str) -> str:
    """Normalised title hash — strips punctuation/whitespace before hashing."""
    clean = re.sub(r'[^\w\s]', '', title.lower())
    clean = re.sub(r'\s+', ' ', clean).strip()
    return hashlib.md5(clean.encode()).hexdigest()


def load_seen(filepath: str) -> set:
    """Load the set of seen URL hashes from disk. Returns empty set if file missing."""
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, "r") as f:
            return set(json.load(f))
    except Exception as e:
        logger.warning(f"[Dedup] Could not load {filepath}: {e}")
        return set()


def save_seen(filepath: str, seen: set):
    """Persist the seen set to disk."""
    try:
        with open(filepath, "w") as f:
            json.dump(list(seen), f, indent=2)
    except Exception as e:
        logger.error(f"[Dedup] Could not save {filepath}: {e}")


def filter_new(articles: list[dict], seen: set) -> tuple[list[dict], set]:
    """
    Return only articles whose normalised URLs haven't been seen before.
    Also updates and returns the seen set (caller must save it after sending).

    NOTE: caller should save_seen() ONLY after a successful send so that
    a failed run does not silently swallow articles.
    """
    new_articles = []
    new_hashes   = []          # collect separately so we add only if article is new
    for art in articles:
        h = _hash(art.get("url", ""))
        if h not in seen:
            new_hashes.append(h)
            new_articles.append(art)
    # Add to seen only after we've decided what's new
    seen.update(new_hashes)
    return new_articles, seen


def deduplicate_within_batch(articles: list[dict]) -> list[dict]:
    """
    Remove duplicate articles within a single batch.

    Deduplication is done on TWO signals:
      1. Normalised URL hash  — catches the same article from different sources
         (e.g., RSS vs Google News redirect for the same page).
      2. Normalised title hash — catches the same story with slightly different
         URLs (e.g., mobile vs desktop, AMP vs canonical).

    The first occurrence of an article wins; later duplicates are dropped.
    """
    seen_url_hashes   = set()
    seen_title_hashes = set()
    unique = []

    for art in articles:
        url   = art.get("url", "")
        title = art.get("title", "")

        uh = _hash(url)
        th = _title_hash(title)

        if uh in seen_url_hashes or th in seen_title_hashes:
            logger.debug(
                f"[Dedup] Batch duplicate dropped: '{title[:60]}' "
                f"(url_match={uh in seen_url_hashes}, "
                f"title_match={th in seen_title_hashes})"
            )
            continue

        seen_url_hashes.add(uh)
        seen_title_hashes.add(th)
        unique.append(art)

    dupes = len(articles) - len(unique)
    if dupes:
        logger.info(f"[Dedup] Removed {dupes} duplicate(s) from batch ({len(unique)} remain).")
    return unique
