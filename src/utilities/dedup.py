# ═══════════════════════════════════════════════════════════════
#  dedup.py  —  Persistent deduplication across runs
#
#  Uses a JSON file (seen_urls.json) to track every URL that has
#  ever been emailed. Delete the file to reset and start fresh.
# ═══════════════════════════════════════════════════════════════

import json
import hashlib
import os
import logging

logger = logging.getLogger(__name__)


def _hash(url: str) -> str:
    """MD5 hash of a normalised URL — used as the stored key."""
    return hashlib.md5(url.strip().lower().encode()).hexdigest()


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
    Return only articles whose URLs haven't been seen before.
    Also updates and returns the seen set (caller must save it after sending).
    """
    new_articles = []
    for art in articles:
        h = _hash(art.get("url", ""))
        if h not in seen:
            seen.add(h)
            new_articles.append(art)
    return new_articles, seen


def deduplicate_within_batch(articles: list[dict]) -> list[dict]:
    """
    Remove duplicate URLs within a single batch
    (same article appearing in multiple sources).
    Also removes duplicates by title (often same story, different URL).
    """
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    for art in articles:
        url_hash = _hash(art.get("url", ""))
        title = art.get("title", "").strip().lower()
        title_hash = hashlib.md5(title.encode()).hexdigest()
        
        # Skip if we've seen this URL or this exact title before
        if url_hash not in seen_urls and title_hash not in seen_titles:
            seen_urls.add(url_hash)
            seen_titles.add(title_hash)
            unique.append(art)
    
    return unique
