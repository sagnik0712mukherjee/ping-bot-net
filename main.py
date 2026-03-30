#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  main.py  —  Pritam News Alerts Bot
#
#  Usage:
#    python main.py               run once, send email if new articles
#    python main.py --schedule    run on a loop every N hours
#    python main.py --dry-run     fetch + print, no email sent
# ═══════════════════════════════════════════════════════════════

import argparse
import logging
import time
from datetime import datetime, timezone
from dateutil import parser as dtp
import config.settings as settings
from src.data_fetch.fetchers import fetch_all
from src.utilities.dedup import load_seen, save_seen, filter_new, deduplicate_within_batch
from src.utilities.emailer import build_html_email, send_email
import src.ai_model.ai_filter as ai_filter

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pritam_monitor")


# ── Core run cycle ────────────────────────────────────────────

def run_once(dry_run: bool = False):
    """Execute a single fetch-filter-send cycle.
    
    Fetches articles from all sources, applies deduplication and AI filtering,
    and sends an email with new articles to recipients. Persists seen URLs
    to prevent duplicate sends across runs.
    
    Args:
        dry_run: If True, print articles and preview email without sending.
    """
    exec_start = time.time()  # Track execution time
    ai_filter.reset_token_usage()  # Reset token tracking
    
    logger.info("=" * 60)
    logger.info("Pritam News Alerts — Starting run")
    logger.info(f"Lookback: {settings.LOOKBACK_M_HOURS}h | Keywords: {len(settings.KEYWORDS)}")
    logger.info("=" * 60)

    # 1. Fetch everything from all sources
    all_articles = fetch_all()
    logger.info(f"Total raw articles: {len(all_articles)}")

    # 2. Deduplicate within this batch (same URL from multiple sources)
    all_articles = deduplicate_within_batch(all_articles)
    logger.info(f"After batch dedup: {len(all_articles)}")

    # 3. AI filter — removes false positives via GPT-4.1
    all_articles = ai_filter.apply_filter(all_articles)
    logger.info(f"After AI filter: {len(all_articles)}")

    # 4. Cross-run dedup (skip already-sent URLs)
    seen = load_seen(settings.SEEN_URLS_FILE)
    new_articles, seen = filter_new(all_articles, seen)
    logger.info(f"New (not previously sent): {len(new_articles)}")

    if not new_articles:
        logger.info("Nothing new to report. Skipping email.")
        return

    # 5. Sort newest first
    def _sort_key(a):
        try:
            return dtp.parse(a["published_at"])
        except Exception:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)

    new_articles.sort(key=_sort_key, reverse=True)

    # 6. Build email
    exec_elapsed = time.time() - exec_start  # Calculate elapsed time
    token_usage = ai_filter.get_token_usage()  # Get token cost info
    
    html    = build_html_email(
        new_articles, 
        settings.LOOKBACK_M_HOURS,
        exec_time=exec_elapsed,
        token_usage=token_usage
    )
    subject = settings.EMAIL_SUBJECT.format(
        date=datetime.now(timezone.utc).strftime("%b %d, %Y")
    )

    if dry_run:
        logger.info("DRY RUN — printing articles, no email sent:")
        for i, a in enumerate(new_articles, 1):
            logger.info(f"  {i:3}. [{a['source']}] {a['title']}")
            logger.info(f"       {a['url']}")
        with open("email_preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Email preview saved → email_preview.html")
        return

    # 7. Send email
    send_email(
        html_body  = html,
        subject    = subject,
        recipients = settings.RECIPIENT_EMAILS,
        smtp_host  = settings.SMTP_HOST,
        smtp_port  = settings.SMTP_PORT,
        smtp_user  = settings.SMTP_USERNAME,
        smtp_pass  = settings.SMTP_PASSWORD,
        from_addr  = settings.EMAIL_FROM,
    )

    # 8. Persist seen URLs only AFTER successful send
    save_seen(settings.SEEN_URLS_FILE, seen)
    logger.info("Run complete.")


# ── Scheduler ─────────────────────────────────────────────────

def run_scheduled():
    """Run the fetch-filter-send cycle repeatedly on a schedule.
    
    Continuously calls run_once() in a loop, sleeping for RUN_EVERY_N_HOURS
    between cycles. Catches and logs exceptions to prevent scheduler crashes.
    """
    logger.info(f"Scheduler mode — running every {settings.RUN_EVERY_N_HOURS}h.")
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f"Run failed: {e}", exc_info=True)
        logger.info(f"Sleeping {settings.RUN_EVERY_N_HOURS}h until next run …")
        time.sleep(settings.RUN_EVERY_N_HOURS * 3600)


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pritam News Alerts Bot")
    parser.add_argument(
        "--schedule", action="store_true",
        help="Run on a loop every N hours (set in settings.py)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch and preview, but do NOT send email."
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        run_once(dry_run=args.dry_run)
