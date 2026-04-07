#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  main.py  —  Pritam News Alerts Bot
#
#  Usage:
#    python main.py               run once, send if new articles
#    python main.py --schedule    loop every N hours
#    python main.py --dry-run     fetch + print, no send
# ═══════════════════════════════════════════════════════════════

import argparse
import logging
import time
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as dtp
import config.settings as settings
from src.data_fetch.fetchers import fetch_all
from src.utilities.dedup import load_seen, save_seen, filter_new, deduplicate_within_batch
from src.utilities.emailer import build_html_email, send_email
import src.ai_model.ai_filter as ai_filter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pritam_monitor")

IST = timezone(timedelta(hours=5, minutes=30))


# ── Telegram ──────────────────────────────────────────────────

def send_telegram(message: str) -> None:
    """Send a Telegram message to ALL configured chat IDs. Silent on failure per recipient."""
    token    = settings.TELEGRAM_BOT_TOKEN
    chat_ids = getattr(settings, "TELEGRAM_CHAT_IDS", [])

    # Back-compat: also honour the old single TELEGRAM_CHAT_ID if CHAT_IDS is missing/empty
    if not chat_ids:
        single = getattr(settings, "TELEGRAM_CHAT_ID", "")
        if single:
            chat_ids = [single]

    if not token or not chat_ids or not getattr(settings, "ENABLE_TELEGRAM", True):
        return

    for chat_id in chat_ids:
        if not chat_id:
            continue
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info(f"[Telegram] ✅ Sent to chat_id {chat_id}.")
            else:
                logger.warning(
                    f"[Telegram] ⚠️ chat_id {chat_id} → "
                    f"Status {resp.status_code}: {resp.text[:100]}"
                )
        except Exception as e:
            logger.warning(f"[Telegram] ⚠️ chat_id {chat_id} failed: {e}")


def build_telegram_digest(articles: list[dict], count_before_filter: int) -> str:
    """Build a compact Telegram message listing new articles."""
    ist_now = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    lines = [f"🎵 <b>Pritam News Alerts</b> — {ist_now}",
             f"<b>{len(articles)}</b> new article(s) found (from {count_before_filter} fetched)\n"]
    for i, art in enumerate(articles[:10], 1):  # cap at 10 for readability
        title  = art.get("title", "Untitled")[:80]
        source = art.get("source", "")
        url    = art.get("url", "#")
        lines.append(f"{i}. <b>{title}</b>\n   [{source}] — <a href=\"{url}\">Read</a>")
    if len(articles) > 10:
        lines.append(f"\n…and {len(articles) - 10} more. Check your email for the full digest.")
    return "\n".join(lines)


# ── Heartbeat (to you only, every run) ────────────────────────

def send_heartbeat(run_number: int, articles_found: int,
                   raw_count: int, exec_secs: float,
                   token_usage: dict) -> None:
    """
    Sends a lightweight status email to RECIPIENT_EMAILS[0] (you) every run,
    regardless of whether news was found. This confirms the bot is alive.
    """
    your_email = settings.RECIPIENT_EMAILS[0]
    ist_now    = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    status_icon = "🟢" if articles_found > 0 else "⚪"

    subject = f"[Pritam Bot] {status_icon} Run #{run_number} — {articles_found} new article(s) — {ist_now}"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:monospace;background:#0d1117;color:#c9d1d9;padding:20px;">
<div style="max-width:480px;margin:0 auto;">
  <h2 style="color:#58a6ff;margin:0 0 16px;">🎵 Pritam Bot — Heartbeat</h2>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="color:#8b949e;padding:4px 0;">Run</td>
        <td style="color:#e6edf3;">#{run_number}</td></tr>
    <tr><td style="color:#8b949e;padding:4px 0;">Time (IST)</td>
        <td style="color:#e6edf3;">{ist_now}</td></tr>
    <tr><td style="color:#8b949e;padding:4px 0;">Raw articles</td>
        <td style="color:#e6edf3;">{raw_count}</td></tr>
    <tr><td style="color:#8b949e;padding:4px 0;">After AI filter</td>
        <td style="color:#{'3fb950' if articles_found > 0 else '8b949e'};font-weight:bold;">{articles_found} new</td></tr>
    <tr><td style="color:#8b949e;padding:4px 0;">Exec time</td>
        <td style="color:#e6edf3;">{exec_secs:.1f}s</td></tr>
    <tr><td style="color:#8b949e;padding:4px 0;">OpenAI cost</td>
        <td style="color:#e6edf3;">${token_usage.get('cost_usd', 0):.5f}
          ({token_usage.get('input_tokens', 0)} in + {token_usage.get('output_tokens', 0)} out tokens)</td></tr>
  </table>
  <p style="margin-top:16px;color:#{'3fb950' if articles_found > 0 else '6e7681'};font-size:13px;">
    {'✅ Digest email sent to all recipients.' if articles_found > 0 else '⚪ No new articles — digest skipped.'}
  </p>
</div>
</body></html>"""

    try:
        send_email(
            html_body  = html,
            subject    = subject,
            recipients = [your_email],
            smtp_host  = settings.SMTP_HOST,
            smtp_port  = settings.SMTP_PORT,
            smtp_user  = settings.SMTP_USERNAME,
            smtp_pass  = settings.SMTP_PASSWORD,
            from_addr  = settings.EMAIL_FROM,
        )
        logger.info(f"[Heartbeat] ✅ Sent to {your_email}")
    except Exception as e:
        logger.warning(f"[Heartbeat] ⚠️ Failed: {e}")

    # NOTE: No Telegram here — Telegram only fires when actual news is found.


# ── Core run cycle ─────────────────────────────────────────────

def run_once(dry_run: bool = False) -> None:
    exec_start = time.time()
    ai_filter.reset_token_usage()

    # Use github run number if available, else timestamp
    import os
    run_number = os.getenv("GITHUB_RUN_NUMBER", datetime.now(IST).strftime("%H%M"))

    logger.info("=" * 60)
    logger.info(f"Pritam News Alerts — Run #{run_number}")
    logger.info(f"Lookback: {settings.LOOKBACK_M_HOURS}h | Keywords: {len(settings.KEYWORDS)}")
    logger.info("=" * 60)

    # 1. Fetch
    all_articles = fetch_all()
    raw_count = len(all_articles)
    logger.info(f"Total raw articles: {raw_count}")

    # 2. Dedup within batch
    all_articles = deduplicate_within_batch(all_articles)
    logger.info(f"After batch dedup: {len(all_articles)}")

    # 3. AI filter
    all_articles = ai_filter.apply_filter(all_articles)
    logger.info(f"After AI filter: {len(all_articles)}")

    # 4. Cross-run dedup
    seen = load_seen(settings.SEEN_URLS_FILE)
    new_articles, seen = filter_new(all_articles, seen)
    logger.info(f"New (not previously sent): {len(new_articles)}")

    # ── IMPORTANT: save seen state NOW, before any sending ──────
    # This guarantees the dedup record is written even if email/Telegram
    # later throws an exception, preventing duplicate sends on the next run.
    if not dry_run:
        save_seen(settings.SEEN_URLS_FILE, seen)
        logger.info("[Dedup] seen_urls.json updated.")

    exec_elapsed = time.time() - exec_start
    token_usage  = ai_filter.get_token_usage()

    # 5. Always send heartbeat to RECIPIENT_EMAILS[0]
    if not dry_run:
        send_heartbeat(run_number, len(new_articles), raw_count, exec_elapsed, token_usage)

    if not new_articles:
        logger.info("Nothing new to report. Heartbeat sent. Done.")
        return

    # 6. Sort newest first
    def _sort_key(a):
        try:
            return dtp.parse(a["published_at"])
        except Exception:
            return datetime(2000, 1, 1, tzinfo=timezone.utc)
    new_articles.sort(key=_sort_key, reverse=True)

    # 7. Build + send digest email to ALL recipients
    html    = build_html_email(new_articles, settings.LOOKBACK_M_HOURS,
                               exec_time=exec_elapsed, token_usage=token_usage)
    subject = settings.EMAIL_SUBJECT.format(
        date=datetime.now(timezone.utc).strftime("%b %d, %Y")
    )

    if dry_run:
        logger.info("DRY RUN — articles:")
        for i, a in enumerate(new_articles, 1):
            logger.info(f"  {i:3}. [{a['source']}] {a['title']}")
            logger.info(f"       {a['url']}")
        with open("email_preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Email preview → email_preview.html")
        return

    try:
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
    except Exception as e:
        logger.error(f"[Email] ❌ Digest send failed: {e} — seen_urls already saved, won't re-send next run.")

    # 8. Send Telegram digest
    tg_msg = build_telegram_digest(new_articles, raw_count)
    send_telegram(tg_msg)

    logger.info("Run complete.")


# ── Scheduler ──────────────────────────────────────────────────

def run_scheduled():
    logger.info(f"Scheduler mode — every {settings.RUN_EVERY_N_HOURS}h.")
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f"Run failed: {e}", exc_info=True)
        logger.info(f"Sleeping {settings.RUN_EVERY_N_HOURS}h …")
        time.sleep(settings.RUN_EVERY_N_HOURS * 3600)


# ── Entry point ────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pritam News Alerts Bot")
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        run_once(dry_run=args.dry_run)