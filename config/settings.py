# ═══════════════════════════════════════════════════════════════
#  PRITAM MONITOR  —  settings.py
#  This is the ONLY file you need to edit.
#  Every tunable in the whole project lives here.
# ═══════════════════════════════════════════════════════════════
import os
# ── Schedule ──────────────────────────────────────────────────
RUN_EVERY_N_HOURS = 4       # How often the bot runs (hours)
LOOKBACK_M_HOURS  = 8       # How far back to look for content (hours)

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

# ── API Keys ───────────────────────────────────────────────────
# NewsAPI — free 100 req/day → https://newsapi.org
NEWSAPI_KEY = "e05d8b48ac3a4b12bbb9d0020951f084"

# GNews — free 100 req/day → https://gnews.io
GNEWS_KEY = "0812a06752dd9a464bff0b545d36bdcf"

# OpenAI — for AI relevance filter → https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Model
OPENAI_MODEL = "gpt-4.1"

# Prompt for OpenAI — dynamically generated from KEYWORDS
def build_ai_filter_prompt() -> str:
    """Build AI filter prompt dynamically based on KEYWORDS list."""
    # Extract film/project names and songs from keywords
    films = [kw for kw in KEYWORDS if any(film in kw.lower() for film in ["bhooth", "cocktail"])]
    films_list = ", ".join(films) if films else "Bhooth Bangla, Cocktail 2"
    
    # Extract song-related keywords (any with common Pritam song titles)
    song_keywords = [kw for kw in KEYWORDS if any(song in kw.lower() for song in ["arijit", "cocktail", "bhooth"])]
    
    return f"""
        You are a relevance filter for a news monitoring bot that tracks Pritam Chakraborty — the famous Bollywood music composer known for Jab We Met, Barfi!, Ae Dil Hai Mushkil, Cocktail, Bhooth Bangla, and many more.

        You will receive a numbered list of articles (title + excerpt). For each one, reply with ONLY "YES" or "NO" on a separate line — one answer per article, in the same order.

        We are currently tracking these keywords: {', '.join(KEYWORDS[:6])}... (and {len(KEYWORDS)-6} more)
        Key film projects: {films_list}
        Related songs: Tu Hi Disda, Ram Ji Aaike, and others from his tracked films

        Reply YES if the article:
        - Directly mentions "Pritam" (the composer) anywhere in title or content
        - Is about a specific Pritam song (e.g., "Tu Hi Disda", "Ram Ji Aaike") — even if PRITAM's name is not explicitly mentioned
        - Discusses movies like {films_list} AND mentions music/songs/soundtrack/composer role (indicates Pritam's artistic contribution)
        - Credits Pritam alongside other musicians (e.g., "Pritam, Arijit Singh, Nikhita G") in a music/song context
        - Mentions any tracked film title WITH keywords like: "song", "music", "soundtrack", "composer", "score", "musical", "singer", "vocal", "score"
        - Is an interview, announcement, or news about Pritam's upcoming release or past work

        Reply NO if the article:
        - Is about a completely different person named Pritam (Pritam Singh the politician, Pritam the footballer, etc.) — check context carefully
        - Mentions a tracked film/project BUT only discusses plot, box office, cast, release dates — no music/film-composer context
        - Is generic Bollywood gossip where Pritam is not the focus
        - Is spam, cocktail recipes, unrelated shopping content, or completely off-topic
        - Mentions "Pritam" only once in passing in an article primarily about someone else

        REMEMBER: If article mentions tracked film names OR tracked songs + music-related context, ACCEPT IT even without explicit "Pritam" mention.
        Accept all Pritam song/soundtrack/film music content. Only YES or NO — no explanations.
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

# ── SMTP / Email ───────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "mukherjeesagnik2@gmail.com"
SMTP_PASSWORD = "lbrlqrhvgyflfjdh"
EMAIL_FROM    = "Pritam Monitor <mukherjeesagnik2@gmail.com>"
EMAIL_SUBJECT = "🎵 Pritam Monitor — Latest Buzz [{date}]"

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
ENABLE_YOUTUBE           = False   # YouTube search + channels (no key)

# Tier 2 — direct named-outlet scrapers (all free, no keys)
ENABLE_TOI               = True    # Times of India / Bombay Times
ENABLE_FILMFARE          = True    # Filmfare
ENABLE_ZOOM              = True    # Zoom TV Entertainment
ENABLE_PINKVILLA         = True    # Pinkvilla
ENABLE_BOLLYWOOD_HUNGAMA = True    # Bollywood Hungama
ENABLE_NDTV              = True    # NDTV Entertainment
ENABLE_IMDB              = True    # IMDB — Pritam's news page (direct scrape)
ENABLE_INSTAGRAM         = True    # Instagram @pritamofficial via Picuki (best-effort)