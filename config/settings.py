# ═══════════════════════════════════════════════════════════════
#  PRITAM MONITOR  —  settings.py
#  This is the ONLY file you need to edit.
# ═══════════════════════════════════════════════════════════════
import os

# ── Schedule ──────────────────────────────────────────────────
RUN_EVERY_N_HOURS = 1       # How often the bot runs (hours)
LOOKBACK_M_HOURS  = 5       # How far back to look (hours) — overlap prevents gaps

# ── Keywords ──────────────────────────────────────────────────
# All keywords with "Pritam" to keep AI filter clean.
# Hashtags and social mentions are now folded in here so they
# benefit from AI filtering instead of being a separate noisy system.
KEYWORDS = [
    "Pritam Chakraborty",
    "Pritam composer",
    "Pritam music director",
    "Pritam Bollywood",
    "Pritam controversy",
    "Pritam plagiarism",
    "Pritam new song",
    "Pritam album",
    "Pritam interview",
    "Pritam Bhooth Bangla",
    "Pritam Arijit",
    "Pritam Cocktail 2",
    "Pritam Aashiqui",
    "Pritam copy",
    "Pritam copied",
    "Pritam Original",
    # Social/hashtag mentions — folded into keywords so AI filter covers them
    "#PritamMusic",
    "#PritamComposer",
    "@ipritamofficial",
]

# ── API Keys (read from environment / GitHub Actions secrets) ──
NEWSAPI_KEY    = os.getenv("NEWSAPI_KEY", "")
GNEWS_KEY      = os.getenv("GNEWS_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = "gpt-4.1"

# ── OpenAI Token Pricing (for cost display in email footer) ────
OPENAI_INPUT_TOKEN_COST  = float(os.getenv("OPENAI_INPUT_TOKEN_COST",  "0.000003"))
OPENAI_OUTPUT_TOKEN_COST = float(os.getenv("OPENAI_OUTPUT_TOKEN_COST", "0.000006"))

# ── AI Filter prompt ───────────────────────────────────────────
def build_ai_filter_prompt() -> str:
    keywords_display = ", ".join(KEYWORDS[:6]) + f"... (and {len(KEYWORDS)-6} more)"
    film_keywords = [kw for kw in KEYWORDS if any(
        f in kw.lower() for f in ["bhooth", "cocktail", "barfi", "jab", "arijit"]
    )]
    films_list = ", ".join(film_keywords) if film_keywords else "tracked projects"
    return f"""You are a relevance filter for a news monitoring bot that tracks Pritam Chakraborty — a famous Bollywood music composer known for Jab We Met, Barfi!, Ae Dil Hai Mushkil, Cocktail, Bhooth Bangla, etc.

You will receive a numbered list of articles (title + excerpt). For each one, reply with ONLY "YES" or "NO" on a separate line — one answer per article, in the same order.

Tracking keywords: {keywords_display}
Key projects: {films_list}

Reply YES if:
- Directly mentions Pritam Chakraborty (the composer) by name
- Is about a specific Pritam song, composition, album, or score
- Discusses a tracked project AND mentions music/songs/soundtrack/composer role
- Is an interview, announcement, or news specifically about Pritam's work

Reply NO if:
- About a different person named Pritam (Pritam Singh politician, Pritam the footballer/Chennaiyin FC)
- Generic Bollywood gossip where Pritam is not the subject
- Spam, recipes, shopping, sports, politics, crime news
- Pritam mentioned only in passing in an article primarily about someone else

Only YES or NO — no explanations."""

DEFAULT_SYSTEM_PROMPT = build_ai_filter_prompt()
AI_FILTER_ENABLED = True

# ── Telegram ────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_TELEGRAM    = True   # set False to disable Telegram notifications

# ── Google Alerts RSS ──────────────────────────────────────────
GOOGLE_ALERTS_RSS_URLS = [
    "https://www.google.com/alerts/feeds/09530471010999255653/5315091837360255028",
    "https://www.google.com/alerts/feeds/09530471010999255653/9086967727411701928",
    "https://www.google.com/alerts/feeds/09530471010999255653/11965898122560387578",
    "https://www.google.com/alerts/feeds/09530471010999255653/10150323239566224244",
    "https://www.google.com/alerts/feeds/09530471010999255653/11066479180287782864",
    "https://www.google.com/alerts/feeds/09530471010999255653/11066479180287781169",
    "https://www.google.com/alerts/feeds/09530471010999255653/10150323239566223068",
    "https://www.google.com/alerts/feeds/09530471010999255653/10150323239566222888",
    "https://www.google.com/alerts/feeds/09530471010999255653/7383859801355997924",
    "https://www.google.com/alerts/feeds/09530471010999255653/14572711428882051808",
    "https://www.google.com/alerts/feeds/09530471010999255653/2840398561910178062",
    "https://www.google.com/alerts/feeds/09530471010999255653/14572711428882054020",
]

# ── YouTube Channel IDs ────────────────────────────────────────
YOUTUBE_CHANNEL_IDS = [
    "UCxxkv3sMgOdVK1cLQPmmH1Q",   # T-Series
    "UCiEGXMH3HQp6FfKc2YdDeFQ",   # Sony Music India
]

# ── Reddit Subreddits ──────────────────────────────────────────
REDDIT_SUBREDDITS = [
    "bollywood",
    "india",
    "hindimusic",
    "music",
    "IndianMusicians",
]

# ── SMTP / Email ───────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "mukherjeesagnik2@gmail.com"
SMTP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
EMAIL_FROM    = "Pritam News Alerts <mukherjeesagnik2@gmail.com>"
EMAIL_SUBJECT = "🎵 Pritam News Alerts — Latest Buzz [{date}]"

RECIPIENT_EMAILS = [
    "mukherjeesagnik2@gmail.com",   # [0] — always receives heartbeat + alerts
    "palashchaturvedi@gmail.com",   # [1] — only receives full digest when news found
]

# ── Dedup file ─────────────────────────────────────────────────
SEEN_URLS_FILE = "seen_urls.json"

# ── Source toggles ─────────────────────────────────────────────
ENABLE_NEWSAPI           = True
ENABLE_GNEWS             = True
ENABLE_GOOGLE_ALERTS_RSS = True
ENABLE_REDDIT            = True
ENABLE_YOUTUBE           = True

ENABLE_TOI               = True
ENABLE_FILMFARE          = True
ENABLE_ZOOM              = True
ENABLE_PINKVILLA         = True
ENABLE_BOLLYWOOD_HUNGAMA = True
ENABLE_NDTV              = True
ENABLE_IMDB              = True
ENABLE_INSTAGRAM         = False   # blocked, revisit later