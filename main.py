
import sys
import argparse
from datetime import datetime
from src.agents.super_agent import build_crew
from src.notification.notifications import push_notification
from src.database import db
from config.settings import NOTIFICATION_EMAIL

def application_init():
    """
    Main monitoring function - runs the search and notification cycle
    """
    result = None
    articles_found = 0
    articles_sent = 0
    duplicates_skipped = 0
    article_urls = []  # Track URLs for marking as sent after email succeeds

    try:
        print("[APP] Starting Pritam News Monitoring Bot...")
        crew_super_agent = build_crew()
        crew_result_str = str(crew_super_agent.kickoff())
        
        # Check if no articles were found
        if "NO_ARTICLES_FOUND" in crew_result_str:
            print(f"\n[APP] No articles found in the last 96 hours. Sending empty notification for testing...")
            result = push_notification("[INFO] No new articles found about Pritam in the last 96 hours.")
            db.log_run(articles_found=0, articles_sent=0, duplicates_skipped=0, status="no_content")
            return "[Result] No articles found - Email sent (testing mode)"
        
        # Parse and store articles in database
        articles_found, article_urls = _process_articles_for_sending(crew_result_str)
        duplicates_skipped = articles_found - len(article_urls)
        articles_sent = len(article_urls)
        
        print(f"\n[APP] Found {articles_found} articles ({duplicates_skipped} duplicates skipped)")
        
        # Only send notification if new articles were found
        if articles_sent > 0:
            print(f"[APP] Processing notification for {articles_sent} new articles...")
            result = push_notification(crew_result_str)
            
            # Only mark as sent if email was successful
            if "Email Sent" in str(result):
                for url, title in article_urls:
                    article_id = db.add_article(
                        url=url,
                        title=title[:100],
                        publish_date=datetime.now().isoformat(),
                        source="Search Results",
                        content_snippet=title,
                        is_controversial='⚠️' in title or 'controversy' in title.lower()
                    )
                    if article_id:
                        db.mark_email_sent(article_id, NOTIFICATION_EMAIL)
                
                print(f"[APP] ✓ Email sent successfully, marked {articles_sent} articles as sent")
                db.log_run(
                    articles_found=articles_found,
                    articles_sent=articles_sent,
                    duplicates_skipped=duplicates_skipped,
                    status="success"
                )
            else:
                # Email failed, don't mark as sent
                print(f"[APP] ✗ Email failed, articles NOT marked as sent")
                db.log_run(
                    articles_found=articles_found,
                    articles_sent=0,
                    duplicates_skipped=duplicates_skipped,
                    status="email_failed"
                )
        else:
            print(f"\n[APP] All {articles_found} articles already sent. Sending update email (testing mode)...")
            result = push_notification(f"[INFO] All {articles_found} articles about Pritam were already sent to you previously.")
            db.log_run(
                articles_found=articles_found,
                articles_sent=0,
                duplicates_skipped=articles_found,
                status="duplicates_only"
            )
            return "[Result] All articles are duplicates - Email sent (testing mode)"
        
    except Exception as e:
        print(f"\n[Fatal Error] Application initialization failed: {str(e)}")
        db.log_run(articles_found=0, articles_sent=0, status="error", error_message=str(e))
        exit(1)
    
    return result


def _count_articles_in_summary(summary: str) -> int:
    """Count number of URLs/articles in the summary"""
    return summary.count("http://") + summary.count("https://")


def _process_articles_for_sending(summary: str) -> tuple:
    """
    Process articles and check for duplicates before sending.
    Returns tuple of (total_articles_found, list_of_new_articles)
    where new_articles = [(url, title), ...]
    """
    # Extract URLs from summary (simplified - looks for http/https patterns)
    lines = summary.split('\n')
    total_articles = 0
    new_articles = []
    
    for line in lines:
        if 'http://' in line or 'https://' in line:
            # Extract URL
            parts = line.split()
            for part in parts:
                if part.startswith('http://') or part.startswith('https://'):
                    url = part.rstrip('')
                    
                    # Try to extract title from nearby text
                    title = line[:100]  # Use first 100 chars of line as title
                    
                    total_articles += 1
                    
                    # Check if article already sent to this recipient
                    if not db.has_been_sent(url, title, NOTIFICATION_EMAIL):
                        new_articles.append((url, title))
                    break  # Only process first URL per line
    
    return total_articles, new_articles


def main():
    """Command-line interface for the bot"""
    parser = argparse.ArgumentParser(description="Pritam News Monitoring Bot")
    parser.add_argument(
        '--mode',
        choices=['once', 'schedule', 'test-email'],
        default='once',
        help='Run mode: once (single run), schedule (background), or test-email (SMTP test)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3,
        help='Scheduler interval in hours (default: 3)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'test-email':
        # Test SMTP connection
        print("[TEST] Testing SMTP connection...")
        try:
            import smtplib
            from config.settings import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, NOTIFICATION_EMAIL
            
            print(f"[TEST] Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            print("[TEST] ✓ Connected!")
            
            print("[TEST] Starting TLS...")
            server.starttls()
            print("[TEST] ✓ TLS started!")
            
            print(f"[TEST] Logging in as {SMTP_EMAIL}...")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            print("[TEST] ✓ Login successful!")
            
            server.quit()
            print("[TEST] ✓ All checks passed! SMTP is working.")
            
        except Exception as e:
            print(f"[TEST] ✗ SMTP test failed: {e}")
            sys.exit(1)
    
    elif args.mode == 'once':
        # Single run mode
        print("[APP] Running in ONE-TIME mode...")
        final_result = application_init()
        print(f"\n\n{'='*70}")
        print(f"[FINAL RESULT] {final_result}")
        print(f"{'='*70}\n")
        
    elif args.mode == 'schedule':
        # Scheduler mode
        print("[APP] Running in SCHEDULED mode...")
        print(f"[APP] Interval: every {args.interval} hours")
        
        try:
            from src.scheduler import scheduler
            
            # Update interval if provided
            if args.interval:
                from config.settings import SCHEDULE_INTERVAL_HOURS
                # Note: This is a simple approach, for production use env vars
                scheduler.scheduler.reschedule_job('pritam_monitoring', 
                                                   trigger=f'interval(hours={args.interval})')
            
            scheduler.start()
            print("[APP] Scheduler started. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[APP] Shutting down scheduler...")
            scheduler.stop()
            print("[APP] Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Scheduler error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()

