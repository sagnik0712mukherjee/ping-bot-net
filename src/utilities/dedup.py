# ═══════════════════════════════════════════════════════════════
#  dedup.py  —  Persistent deduplication across runs
#
#  Uses a JSON file (seen_urls.json) to track every URL and title
#  that has been emailed. Delete the file to reset and start fresh.
#
#  Key design: ALL dedup (batch + persistent) works on:
#  1. Normalised URL hash — catches same article from different sources
#  2. Normalised title hash — catches same story with different URLs
#
#  This ensures the same article from Bollywood Hungama RSS, Google
#  Alerts, Times of India, etc. won't be sent twice.
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


def load_seen(filepath: str) -> dict:
    """Load the set of seen URL hashes and title hashes from disk.
    
    Returns dict with keys 'urls' and 'titles' containing sets.
    Returns empty dict with empty sets if file missing.
    """
    if not os.path.exists(filepath):
        return {"urls": set(), "titles": set()}
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            # Handle both old format (list) and new format (dict)
            if isinstance(data, list):
                # Old format: list of URL hashes only
                return {"urls": set(data), "titles": set()}
            else:
                # New format: dict with 'urls' and 'titles' keys
                return {
                    "urls": set(data.get("urls", [])),
                    "titles": set(data.get("titles", []))
                }
    except Exception as e:
        logger.warning(f"[Dedup] Could not load {filepath}: {e}")
        return {"urls": set(), "titles": set()}


def save_seen(filepath: str, seen: dict):
    """Persist the seen dict (with 'urls' and 'titles' sets) to disk."""
    try:
        data = {
            "urls": list(seen.get("urls", set())),
            "titles": list(seen.get("titles", set()))
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"[Dedup] Could not save {filepath}: {e}")


def filter_new(articles: list[dict], seen: dict) -> tuple[list[dict], dict]:
    """
    Return only articles whose normalised URLs or titles haven't been seen before.
    Also updates and returns the seen dict with both URL and title hashes.

    NOTE: caller should save_seen() ONLY after a successful send so that
    a failed run does not silently swallow articles.
    
    Args:
        articles: List of article dicts
        seen: Dict with keys 'urls' and 'titles', each containing sets of hashes
        
    Returns:
        Tuple of (new_articles list, updated seen dict)
    """
    new_articles = []
    new_url_hashes = []
    new_title_hashes = []
    
    seen_urls = seen.get("urls", set())
    seen_titles = seen.get("titles", set())
    
    for art in articles:
        url = art.get("url", "")
        title = art.get("title", "")
        
        url_hash = _hash(url)
        title_hash = _title_hash(title)
        
        # Check if we've seen this article by URL OR by title
        if url_hash in seen_urls or title_hash in seen_titles:
            logger.debug(
                f"[Dedup] Cross-run duplicate dropped: '{title[:60]}' "
                f"(url_match={url_hash in seen_urls}, "
                f"title_match={title_hash in seen_titles})"
            )
            continue
        
        new_url_hashes.append(url_hash)
        new_title_hashes.append(title_hash)
        new_articles.append(art)
    
    # Update seen with new hashes
    seen["urls"].update(new_url_hashes)
    seen["titles"].update(new_title_hashes)
    
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
    duplicates = []

    for art in articles:
        url   = art.get("url", "")
        title = art.get("title", "")

        uh = _hash(url)
        th = _title_hash(title)

        if uh in seen_url_hashes or th in seen_title_hashes:
            dup_type = "URL" if uh in seen_url_hashes else "Title"
            duplicates.append(f"  - {title[:70]} ({dup_type})")
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
        if duplicates and len(duplicates) <= 10:
            logger.info("  Duplicates dropped:\n" + "\n".join(duplicates))
    return unique
