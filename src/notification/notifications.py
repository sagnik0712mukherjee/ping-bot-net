import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config.settings import (
    SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, 
    NOTIFICATION_EMAIL, EMAIL_SUBJECT_PREFIX, 
    MAX_EMAIL_RETRIES, EMAIL_RETRY_DELAY
)


def push_notification(notification_message: str) -> str:
    """
    Main notification dispatcher. Routes to email if content exists,
    skips if NO_ARTICLES_FOUND.
    
    Args:
        notification_message (str): The summary message from the agent
        
    Return:
        Status message indicating what action was taken
    """
    
    # Check if no articles were found
    if "NO_ARTICLES_FOUND" in notification_message:
        return "[Notification] No articles found - Email not sent"
    
    # Trim empty or very short messages
    if not notification_message or len(notification_message.strip()) < 20:
        return "[Notification] Empty summary - Email not sent"
    
    # Send email notification
    return send_email_notification(notification_message)


def send_email_notification(summary: str) -> str:
    """
    Send email notification with the summary. Includes retry logic.
    
    Args:
        summary (str): The article summary to send
        
    Return:
        Status message with success/failure details
    """
    
    # Check if email configuration is complete
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFICATION_EMAIL:
        log_message = "[Email Notification] Email configuration incomplete. Summary logged instead:\n"
        print(log_message)
        print(summary[:500])
        return f"{log_message}(Configuration missing - logged to console)"
    
    # Prepare email content
    subject = _generate_subject()
    html_body = _generate_html_email(summary)
    text_body = _generate_text_email(summary)
    
    # Attempt to send with retries
    for attempt in range(1, MAX_EMAIL_RETRIES + 1):
        try:
            print(f"\n[Email] Attempt {attempt}/{MAX_EMAIL_RETRIES} to send notification to {NOTIFICATION_EMAIL}...")
            _send_smtp_email(subject, html_body, text_body)
            return f"[Email Sent ✓] Successfully sent to {NOTIFICATION_EMAIL}"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[Email Error - Attempt {attempt}] {error_msg}")
            
            if attempt < MAX_EMAIL_RETRIES:
                print(f"[Email] Retrying in {EMAIL_RETRY_DELAY} seconds...")
                time.sleep(EMAIL_RETRY_DELAY)
            else:
                return f"[Email Failed ✗] After {MAX_EMAIL_RETRIES} attempts: {error_msg}"
    
    return "[Email Failed ✗] Unexpected error in retry loop"


def _send_smtp_email(subject: str, html_body: str, text_body: str) -> None:
    """
    Send email via SMTP. Supports Gmail, Outlook, and custom SMTP servers.
    
    Args:
        subject (str): Email subject
        html_body (str): HTML formatted email body
        text_body (str): Plain text email body
        
    Raises:
        Exception: If SMTP connection or sending fails
    """
    
    print(f"[Email Debug] Using SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"[Email Debug] From: {SMTP_EMAIL}")
    print(f"[Email Debug] To: {NOTIFICATION_EMAIL}")
    
    # Create message with multipart (text + HTML)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = NOTIFICATION_EMAIL
    
    # Attach text and HTML versions
    part_text = MIMEText(text_body, "plain")
    part_html = MIMEText(html_body, "html")
    msg.attach(part_text)
    msg.attach(part_html)
    
    print(f"[Email Debug] Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    
    # Connect and send
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            print(f"[Email Debug] Connected! Starting TLS...")
            server.starttls()  # Enable encryption (TLS)
            
            print(f"[Email Debug] Logging in with: {SMTP_EMAIL}")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            
            print(f"[Email Debug] Sending email...")
            result = server.sendmail(SMTP_EMAIL, NOTIFICATION_EMAIL, msg.as_string())
            print(f"[Email Debug] Send result: {result}")
        
        print(f"[Email] ✓ Successfully connected, authenticated, and sent to {NOTIFICATION_EMAIL}")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[Email Debug] Authentication error: {e}")
        raise Exception(f"SMTP Authentication failed: {e}")
    except smtplib.SMTPException as e:
        print(f"[Email Debug] SMTP error: {e}")
        raise Exception(f"SMTP error: {e}")
    except Exception as e:
        print(f"[Email Debug] General error: {e}")
        raise


def _generate_subject() -> str:
    """Generate email subject with timestamp"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{EMAIL_SUBJECT_PREFIX} - {now}"


def _generate_text_email(summary: str) -> str:
    """Generate plain text version of email"""
    return f"""
Pritam News Monitoring Alert
=============================

Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUMMARY:
--------

{summary}

---
This is an automated notification from Ping Bot.
Last 96 hours of coverage from multiple sources (DuckDuckGo, Bing, Reddit)
"""


def _generate_html_email(summary: str) -> str:
    """Generate HTML formatted email with styling"""
    
    # Extract key information from summary
    has_controversy = "⚠️" in summary or "CONTROVERSY" in summary.upper()
    article_count = summary.count("http") if "http" in summary else 0
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build HTML
    html = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .container {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .meta {{
                    background-color: #e8f4f8;
                    padding: 12px;
                    border-left: 4px solid #667eea;
                    margin-bottom: 20px;
                    border-radius: 4px;
                }}
                .meta-item {{
                    margin: 5px 0;
                    font-size: 14px;
                }}
                .alert-flag {{
                    background-color: #fff3cd;
                    border: 2px solid #ffb81c;
                    color: #753210;
                    padding: 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    font-weight: bold;
                }}
                .content {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    border: 1px solid #eee;
                }}
                .content pre {{
                    background-color: #f5f5f5;
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-size: 13px;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
                .controversy-marker {{
                    color: #d32f2f;
                    font-weight: bold;
                }}
                a {{
                    color: #667eea;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎬 Pritam News Alert</h1>
                    <p>Automated Monitoring Report</p>
                </div>
                
                <div class="meta">
                    <div class="meta-item"><strong>Generated:</strong> {timestamp}</div>
                    <div class="meta-item"><strong>Period:</strong> Last 96 hours</div>
                    <div class="meta-item"><strong>Articles Found:</strong> {article_count}</div>
                    {'<div class="meta-item"><strong style="color: #d32f2f;">⚠️ Contains Controversial Content</strong></div>' if has_controversy else ''}
                </div>
                
                {'<div class="alert-flag">⚠️ CONTROVERSY ALERT: This report contains controversial or negative information about Pritam</div>' if has_controversy else ''}
                
                <div class="content">
                    <h2>📰 Summary</h2>
                    <pre>{_escape_html(summary)}</pre>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from Ping Bot - Pritam Monitoring System</p>
                    <p>Searches across: DuckDuckGo, Bing, Reddit | Updates every 3-4 hours</p>
                    <p><a href="#">Manage Preferences</a> | <a href="#">Unsubscribe</a></p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html


def _escape_html(text: str) -> str:
    """Escape special HTML characters"""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    return text
