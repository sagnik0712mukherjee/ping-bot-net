"""
ai_filter.py  —  GPT-4.1 relevance filter for Pritam Monitor.

Called by main.py AFTER fetch_all() + dedup.
Takes raw articles, returns only those genuinely about Pritam Chakraborty.

Usage:
    from ai_filter import apply_filter
    clean_articles = apply_filter(raw_articles)

Requirements:
    pip install openai

Configuration (in settings.py):
    OPENAI_API_KEY  — your OpenAI API key
    AI_FILTER_ENABLED — True/False toggle (default True)
"""

import logging
import config.settings as settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Prompt — read from settings if overridden, else use this default
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_SYSTEM_PROMPT = settings.DEFAULT_SYSTEM_PROMPT


def _get_system_prompt() -> str:
    """Retrieve the AI filter system prompt from settings or use default.
    
    Returns the custom AI_FILTER_PROMPT from settings if defined,
    otherwise uses the dynamically generated DEFAULT_SYSTEM_PROMPT.
    """
    return getattr(settings, "AI_FILTER_PROMPT", _DEFAULT_SYSTEM_PROMPT)


def _get_api_key() -> str:
    """Retrieve the OpenAI API key from settings.
    
    Returns the OPENAI_API_KEY from settings, or empty string if not set.
    """
    return getattr(settings, "OPENAI_API_KEY", "")


def _is_enabled() -> bool:
    """Check if AI filtering is enabled in settings.
    
    Returns True if AI_FILTER_ENABLED is set in settings, defaults to True.
    """
    return getattr(settings, "AI_FILTER_ENABLED", True)


# ─────────────────────────────────────────────────────────────────────────────
#  Core filter
# ─────────────────────────────────────────────────────────────────────────────

def apply_filter(articles: list[dict]) -> list[dict]:
    """
    Sends articles to GPT-4.1 in batches of 15.
    Returns only articles that GPT says are genuinely about Pritam.

    Falls back to returning all articles if:
    - AI_FILTER_ENABLED is False in settings
    - OPENAI_API_KEY is not set
    - openai package is not installed
    - API call fails
    """
    if not _is_enabled():
        logger.info("[AI Filter] Disabled in settings — passing all articles through.")
        return articles

    if not articles:
        return articles

    api_key = _get_api_key()
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        logger.warning("[AI Filter] No OPENAI_API_KEY in settings — skipping filter.")
        logger.warning("[AI Filter] Add OPENAI_API_KEY to settings.py to enable filtering.")
        return articles

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("[AI Filter] openai not installed — run: pip install openai")
        return articles

    kept      = []
    batch_size = 15
    system    = _get_system_prompt()

    logger.info(f"\n\n\n[AI Filter] Filtering {len(articles)} articles with GPT-4.1 ...\n\n")

    for i in range(0, len(articles), batch_size):
        chunk = articles[i : i + batch_size]

        # Build numbered list for GPT
        lines = []
        for j, art in enumerate(chunk, 1):
            title   = art.get("title", "").strip()
            excerpt = (art.get("excerpt") or "")[:300].strip()
            source  = art.get("source", "")
            lines.append(
                f"{j}. [{source}]\n"
                f"   TITLE: {title}\n"
                f"   EXCERPT: {excerpt}"
            )

        user_msg = (
            "For each article below, reply YES or NO (one per line, in order):\n\n"
            + "\n\n".join(lines)
        )

        try:
            resp = client.chat.completions.create(
                model    = settings.OPENAI_MODEL,
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_msg},
                ],
                max_tokens      = 60,   # 15 articles × 4 chars ("YES\n") = well under 60
                temperature     = 0,    # deterministic — no creativity needed
            )
            raw_answers = resp.choices[0].message.content.strip().upper()
            answers = [
                line.strip()
                for line in raw_answers.split("\n")
                if line.strip() in ("YES", "NO")
            ]

            for j, art in enumerate(chunk):
                if j < len(answers):
                    verdict = answers[j]
                else:
                    verdict = "YES"   # if GPT returned fewer answers than articles, keep
                    logger.warning(f"[AI Filter] No answer for article {i+j+1} — keeping by default")

                if verdict == "YES":
                    kept.append(art)
                else:
                    logger.info(f"[AI Filter] ✗ REJECTED: [{art.get('source','')}] {art.get('title','')[:80]}")

        except Exception as e:
            logger.warning(f"[AI Filter] API error on batch {i//batch_size + 1}: {e} — keeping batch unfiltered")
            kept.extend(chunk)

    logger.info(f"[AI Filter] ✅ {len(kept)}/{len(articles)} articles passed.")
    return kept
