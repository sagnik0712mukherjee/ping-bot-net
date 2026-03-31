# ═══════════════════════════════════════════════════════════════
#  PRITAM MONITOR  —  settings.py
#  This is the ONLY file you need to edit.
#  Every tunable in the whole project lives here.
# ═══════════════════════════════════════════════════════════════
import os
# ── Schedule ──────────────────────────────────────────────────
RUN_EVERY_N_HOURS = 1       # How often the bot runs (hours)
LOOKBACK_M_HOURS  = 5       # How far back to look for content (hours)

# ── Keywords ──────────────────────────────────────────────────
KEYWORDS = [
    # ── Core identity keywords (all contain "Pritam" — tight, no false positives)
    "Pritam Chakraborty",
    "Pritam composer",
    "Pritam music director",
    "Pritam Bollywood",
    "Pritam controversy",
    "Pritam plagiarism",
    "Pritam new song",
    "Pritam album",
    "Pritam interview",
    "Pritam Bhooth Bangla",      # current film — keeps "Pritam" in the query
    "Pritam Arijit",             # common co-credit pairing
    "Pritam Cocktail 2",         # upcoming project — keeps "Pritam" in query
]

# ── API Keys (read from GitHub Actions secrets / environment variables) ───────────────────────────────────────────────
# NewsAPI — free 100 req/day → https://newsapi.org
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# GNews — free 100 req/day → https://gnews.io (optional)
GNEWS_KEY = os.getenv("GNEWS_KEY", "")

# OpenAI — for AI relevance filter → https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI Model
OPENAI_MODEL = "gpt-4.1"

# ── GPT-4.1 Token Pricing (for cost tracking) ────────────────────────────────
# As of March 2025: $0.003 per 1K input tokens, $0.006 per 1K output tokens
# Read from env vars (so you can change without code edit)
OPENAI_INPUT_TOKEN_COST = float(os.getenv("OPENAI_INPUT_TOKEN_COST", "0.000003"))   # per token (div 1000)
OPENAI_OUTPUT_TOKEN_COST = float(os.getenv("OPENAI_OUTPUT_TOKEN_COST", "0.000006"))  # per token (div 1000)

# Prompt for OpenAI — dynamically generated from KEYWORDS
def build_ai_filter_prompt() -> str:
    """Build AI filter prompt dynamically based on KEYWORDS list."""
    # Extract all keywords for the prompt
    keywords_display = ", ".join(KEYWORDS[:6]) + f"... (and {len(KEYWORDS)-6} more)" if len(KEYWORDS) > 6 else ", ".join(KEYWORDS)
    
    # Extract film/project names from keywords (any with "Pritam" + film keywords)
    film_keywords = [kw for kw in KEYWORDS if any(film in kw.lower() for film in ["bhooth", "cocktail", "barfi", "jab", "arijit"])]
    films_list = ", ".join(film_keywords) if film_keywords else "tracked projects"
    
    return f"""
        You are a relevance filter for a news monitoring bot that tracks Pritam Chakraborty — a famous Bollywood music composer.

        You will receive a numbered list of articles (title + excerpt). For each one, reply with ONLY "YES" or "NO" on a separate line — one answer per article, in the same order.

        We are currently tracking these keywords: {keywords_display}
        Key tracked projects: {films_list}

        Reply YES if the article:
        - Directly mentions "Pritam" (the composer) anywhere in title or content
        - Is about a specific Pritam song or music composition — even without explicit "Pritam" mention
        - Discusses any of the tracked projects/keywords AND mentions music/songs/soundtrack/composer role
        - Credits Pritam alongside other musicians in a music/song context
        - Mentions any tracked keyword WITH music-related terms: "song", "music", "soundtrack", "composer", "score", "musical", "singer", "vocal", "album"
        - Is an interview, announcement, or news about Pritam's work

        Reply NO if the article:
        - Is about a completely different person named Pritam
        - Mentions tracked keywords BUT only discusses plot, box office, cast, release dates — no music/composer context
        - Is generic gossip where Pritam is not the focus
        - Is spam, unrelated recipes, shopping content, or off-topic
        - Mentions "Pritam" only in passing in an article primarily about someone else

        REMEMBER: If article mentions tracked keywords/projects + music-related context, ACCEPT IT even without explicit "Pritam" name.
        Accept all music-related content. Only YES or NO — no explanations.
    """

# Default prompt (kept for compatibility)
DEFAULT_SYSTEM_PROMPT = build_ai_filter_prompt()

# ── AI Filter ──────────────────────────────────────────────────
# GPT-4.1 scans every article after fetch and removes anything not
# genuinely about Pritam Chakraborty the composer.
AI_FILTER_ENABLED = True

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
    "https://www.google.com/alerts/feeds/09530471010999255653/14572711428882054020"
]

# ── YouTube Channel IDs to monitor directly ────────────────────
# These channels are fetched via public RSS — no key needed.
YOUTUBE_CHANNEL_IDS = [
    "UCxxkv3sMgOdVK1cLQPmmH1Q",   # T-Series (Pritam's primary label)
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

# ── Twitter/X Monitoring ──────────────────────────────────────
# Monitor @pritamofficial and related accounts + search mentions
TWITTER_ACCOUNTS = [
    "ipritamofficial",
]

TWITTER_SEARCH_TERMS = [
    "Pritam Chakraborty",
    "Pritam music",
    "Pritam songs",
    "@pritamofficial",
]

# ── Hashtag Monitoring via Google News ────────────────────────
# Search for these hashtags to find fan posts, music releases, etc.
HASHTAGS = [
    "#PritamMusic",
    "#PritamComposer",
    "#PritamSongs",
    "#BhootBangla",
    "#Cocktail2",
]

# ── SMTP / Email (read from GitHub Actions secrets / environment variables) ───────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "mukherjeesagnik2@gmail.com"
SMTP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
EMAIL_FROM    = "Pritam News Alerts <mukherjeesagnik2@gmail.com>"
EMAIL_SUBJECT = "🎵 Pritam News Alerts — Latest Buzz [{date}]"

RECIPIENT_EMAILS = [
    "mukherjeesagnik2@gmail.com",
    "palashchaturvedi@gmail.com"
]

# ── Dedup file ─────────────────────────────────────────────────
# JSON file that tracks all sent URLs. Auto-created on first run.
# Delete this file to reset and re-send all articles from scratch.
SEEN_URLS_FILE = "seen_urls.json"

# ── Source toggles ─────────────────────────────────────────────
# Set any to False to disable that source.

# Tier 1 — keyword-driven broad sources
ENABLE_NEWSAPI           = True    # NewsAPI        (free key needed)
ENABLE_GNEWS             = False   # GNews API      (free key needed) — DISABLED: 403 errors
ENABLE_GOOGLE_ALERTS_RSS = True    # Google Alerts  (manual setup, no key)
ENABLE_REDDIT            = True    # Reddit RSS     (no key)
ENABLE_YOUTUBE           = False   # YouTube search + channels + Shorts (Piped API unstable — temporarily disabled)

# Tier 2 — direct named-outlet scrapers (all free, no keys)
ENABLE_TOI               = True    # Times of India / Bombay Times
ENABLE_FILMFARE          = True    # Filmfare
ENABLE_ZOOM              = True    # Zoom TV Entertainment
ENABLE_PINKVILLA         = True    # Pinkvilla
ENABLE_BOLLYWOOD_HUNGAMA = True    # Bollywood Hungama
ENABLE_NDTV              = True    # NDTV Entertainment
ENABLE_IMDB              = True    # IMDB — Pritam's news page (direct scrape)
ENABLE_INSTAGRAM         = False   # Instagram @pritamofficial (currently blocked, revisit later)
ENABLE_TWITTER           = True    # Twitter/X mentions & accounts
ENABLE_HASHTAGS          = True    # Hashtag search via Google News