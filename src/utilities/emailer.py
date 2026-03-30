# ═══════════════════════════════════════════════════════════════
#  emailer.py  —  Build & send styled HTML digest email
# ═══════════════════════════════════════════════════════════════

import smtplib
import ssl
import logging
from collections import Counter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from datetime import timezone, timedelta, datetime
from dateutil import parser as dtp
from datetime import timezone, timedelta

logger = logging.getLogger(__name__)

# ── Source badge colours ──────────────────────────────────────
_SOURCE_COLORS = {
    "Google News":                  ("#e8f5e9", "#2e7d32"),
    "Google Alerts":                ("#e3f2fd", "#1565c0"),
    "NewsAPI":                      ("#fff3e0", "#e65100"),
    "GNews":                        ("#fff8e1", "#f57f17"),
    "Reddit":                       ("#fce4ec", "#c62828"),
    "Twitter":                      ("#e1f5fe", "#0288d1"),
    "Hashtag":                      ("#f3e5f5", "#7b1fa2"),
    "YouTube":                      ("#ffebee", "#b71c1c"),
    "YouTube Shorts":               ("#ffcdd2", "#d32f2f"),
    "Times of India":               ("#e8eaf6", "#283593"),
    "Filmfare":                     ("#fdf6e3", "#8d6418"),
    "Zoom TV Entertainment":        ("#f3e5f5", "#6a1b9a"),
    "Pinkvilla":                    ("#fce4ec", "#880e4f"),
    "Bollywood Hungama":            ("#fff3e0", "#bf360c"),
    "NDTV Entertainment":           ("#ffebee", "#b71c1c"),
    "IMDB":                         ("#fffde7", "#827717"),
    "Instagram (@pritamofficial)":  ("#fce4ec", "#ad1457"),
}

def _badge(source: str) -> str:
    """Generate HTML badge for article source with colors.
    
    Args:
        source: Name of the article source.
        
    Returns:
        HTML string for a styled source badge.
    """
    bg, fg = "#f3f4f6", "#374151"
    for key, (b, f) in _SOURCE_COLORS.items():
        if source.startswith(key):
            bg, fg = b, f
            break
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 9px;'
        f'border-radius:10px;font-size:11px;font-weight:700;'
        f'letter-spacing:0.4px;">{source}</span>'
    )


def _fmt_date(iso_str: str) -> str:
    """Format an ISO datetime string to human-readable format in IST.
    
    Args:
        iso_str: ISO 8601 format datetime string (UTC).
        
    Returns:
        Formatted date string in IST (e.g. "Mar 15, 2026 · 10:30 AM IST") or "—" if empty.
    """
    if not iso_str:
        return "—"
    try:
        dt = dtp.parse(iso_str)
        # Convert UTC to IST (UTC+5:30)
        ist = timezone(timedelta(hours=5, minutes=30))
        dt_ist = dt.astimezone(ist)
        return dt_ist.strftime("%b %d, %Y · %I:%M %p IST")
    except Exception:
        return iso_str


# ── HTML builder ──────────────────────────────────────────────

def build_html_email(articles: list[dict], lookback_hours: int) -> str:
    """Build a styled HTML email from a list of articles.
    
    Creates a professional HTML email digest with article cards, source breakdown,
    and formatted styling in IST timezone.
    
    Args:
        articles: List of article dictionaries with keys: title, url, source, excerpt, published_at.
        lookback_hours: Number of hours this batch covers (for display).
        
    Returns:
        Complete HTML email as a string.
    """
    ist = timezone(timedelta(hours=5, minutes=30))
    now_str = datetime.now(ist).strftime("%B %d, %Y at %I:%M %p IST")
    count   = len(articles)

    # Source breakdown pills
    source_counts = Counter(a["source"] for a in articles)
    pills = "".join(
        f'<span style="display:inline-block;background:#fff;border:1px solid #e0e0e0;'
        f'border-radius:20px;padding:3px 11px;margin:3px;font-size:12px;color:#555;">'
        f'<b style="color:#1a1a1a;">{cnt}</b>&nbsp;{src}</span>'
        for src, cnt in source_counts.most_common()
    )

    # Article cards
    cards = ""
    for i, art in enumerate(articles, 1):
        title   = (art.get("title") or "Untitled").replace("<","&lt;").replace(">","&gt;")
        url     = art.get("url", "#")
        source  = art.get("source", "Unknown")
        pub     = _fmt_date(art.get("published_at", ""))
        excerpt = (art.get("excerpt") or "").replace("<","&lt;").replace(">","&gt;")
        badge   = _badge(source)

        excerpt_row = (
            f'<p style="margin:10px 0 0;font-size:14px;color:#555;line-height:1.65;">'
            f'{excerpt}</p>'
            if excerpt else ""
        )

        cards += f"""
        <tr>
          <td style="padding:0 0 16px 0;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fff;border:1px solid #e8e8e8;
                          border-radius:10px;overflow:hidden;">
              <tr>
                <td style="padding:18px 22px 14px 22px;">
                  <!-- Number + Title -->
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="width:32px;vertical-align:top;padding-right:10px;">
                        <span style="display:inline-block;width:26px;height:26px;
                                     background:#1a1a2e;color:#fff;border-radius:50%;
                                     text-align:center;line-height:26px;
                                     font-size:12px;font-weight:700;">{i}</span>
                      </td>
                      <td style="vertical-align:top;">
                        <a href="{url}"
                           style="font-size:16px;font-weight:700;color:#1a1a2e;
                                  text-decoration:none;line-height:1.4;display:block;">
                          {title}
                        </a>
                      </td>
                    </tr>
                  </table>
                  <!-- Badge + Date -->
                  <table width="100%" cellpadding="0" cellspacing="0"
                         style="margin-top:10px;">
                    <tr>
                      <td>{badge}</td>
                      <td align="right" style="font-size:11px;color:#999;">{pub}</td>
                    </tr>
                  </table>
                  {excerpt_row}
                  <!-- CTA button -->
                  <table cellpadding="0" cellspacing="0" style="margin-top:14px;">
                    <tr>
                      <td style="background:#1a1a2e;border-radius:5px;">
                        <a href="{url}"
                           style="display:inline-block;padding:7px 16px;
                                  color:#fff;font-size:13px;font-weight:600;
                                  text-decoration:none;">
                          Read Article →
                        </a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    if not cards:
        cards = """
        <tr><td style="padding:40px;text-align:center;color:#999;font-size:15px;">
          No new mentions found in this period.
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f4f4f7;
             font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f4f4f7;padding:30px 0;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0"
             style="max-width:620px;width:100%;">

        <!-- HEADER -->
        <tr>
          <td style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
                     border-radius:12px 12px 0 0;padding:32px 30px 28px;">
            <p style="margin:0 0 6px;font-size:12px;color:#a0aec0;
                      letter-spacing:2px;text-transform:uppercase;font-weight:600;">
              Automated Digest
            </p>
            <h1 style="margin:0;font-size:26px;color:#fff;
                       font-weight:800;letter-spacing:-0.5px;">
              🎵 Pritam Monitor
            </h1>
            <p style="margin:8px 0 0;font-size:13px;color:#a0aec0;">
              Last <b style="color:#fff;">{lookback_hours}h</b> · {now_str}
            </p>
          </td>
        </tr>

        <!-- STATS BAR -->
        <tr>
          <td style="background:#16213e;padding:14px 30px;">
            <span style="font-size:13px;color:#a0aec0;">
              <b style="font-size:22px;color:#e94560;">{count}</b>&nbsp; new mentions found
            </span>
            <div style="margin-top:8px;">{pills}</div>
          </td>
        </tr>

        <!-- ARTICLES -->
        <tr>
          <td style="background:#f4f4f7;padding:20px 20px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {cards}
            </table>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="background:#e8e8ed;border-radius:0 0 12px 12px;
                     padding:18px 30px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#888;line-height:1.6;">
              Auto-generated by <b>Pritam Monitor Bot</b>.<br>
              Sources: Google News · Google Alerts · NewsAPI · GNews ·
              Reddit · YouTube · TOI · Filmfare · Zoom · Pinkvilla ·
              Hungama · NDTV · IMDB · Instagram<br>
              <span style="color:#aaa;">
                To unsubscribe, remove your email from settings.py
              </span>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

</body>
</html>"""


# ── Sender ────────────────────────────────────────────────────

def send_email(
    html_body:  str,
    subject:    str,
    recipients: list[str],
    smtp_host:  str,
    smtp_port:  int,
    smtp_user:  str,
    smtp_pass:  str,
    from_addr:  str,
):
    """Send an HTML email via SMTP.
    
    Constructs a multipart MIME email and sends it through the specified
    SMTP server with TLS encryption.
    
    Args:
        html_body: HTML content of the email.
        subject: Email subject line.
        recipients: List of recipient email addresses.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_user: SMTP login username.
        smtp_pass: SMTP login password.
        from_addr: Sender email address.
        
    Raises:
        Exception: If SMTP connection or send fails.
    """
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText("Your email client does not support HTML emails.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, recipients, msg.as_string())
        logger.info(f"[Email] ✅ Sent to {len(recipients)} recipient(s).")
    except Exception as e:
        logger.error(f"[Email] ❌ Failed: {e}")
        raise
