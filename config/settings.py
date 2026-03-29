# Imports
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"  # config/ -> ping-bot-net/ -> .env
print(f"\n[Config] Looking for .env at: {env_path}")
print(f"[Config] .env exists: {env_path.exists()}")

if env_path.exists():
    result = load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"[Config] .env loaded: {result}")
else:
    print(f"[Config] WARNING: .env file not found at {env_path}")

# API Keys
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# LLM Models
search_llm_model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
summariser_llm_model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)

# Search Keywords
# Search Keywords - Comprehensive tracking of Pritam, his songs, albums, movies, and controversies
# OPTIMIZED: Core keywords only to speed up searches
search_keywords = [
    # Direct Pritam references
    "Pritam",
    "Pritam Chakraborty",
    "Pritam music director",
    
    # Pritam's most famous songs
    "Tu Hi Disda",
    
    # Controversies and news
    "Pritam controversy",
]

# Search Domains - Expand to cover all major entertainment sites
search_domains = [
    "filmfare.com",
    "thehindu.com",
    "deccanchronicle.com",
    "bollywoodhungama.com",
    "imdb.com",
    "zoomtventertainment.com",
    "indiatoday.in",
    "hindustantimes.com",
    "mumbaimirror.com",
]

# Search top k results
top_k = 20

# Path for all MD files related to the task
task_data_path = "data"

# Ensure data directory exists
os.makedirs(task_data_path, exist_ok=True)

# ==================== EMAIL NOTIFICATION SETTINGS ====================

# SMTP Configuration (Gmail/Outlook)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # Default: Gmail
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # Default: TLS port
SMTP_EMAIL = os.getenv("SMTP_EMAIL")  # Sender email (required)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # App password (required)

# Notification Configuration
NOTIFICATION_EMAIL_RAW = os.getenv("NOTIFICATION_EMAIL")  # Can be comma-separated list
# Parse comma-separated emails into a list
NOTIFICATION_EMAILS = [
    email.strip() 
    for email in NOTIFICATION_EMAIL_RAW.split(',') 
    if email.strip()
] if NOTIFICATION_EMAIL_RAW else []
NOTIFICATION_EMAIL = NOTIFICATION_EMAILS[0] if NOTIFICATION_EMAILS else None  # Primary email for backward compatibility
EMAIL_SUBJECT_PREFIX = "🎬 Pritam News Alert"

# Email Retry Configuration
MAX_EMAIL_RETRIES = 3
EMAIL_RETRY_DELAY = 2  # seconds

print(f"\n[Config] Email Settings:")
print(f"  - SMTP_SERVER: {SMTP_SERVER}")
print(f"  - SMTP_PORT: {SMTP_PORT}")
print(f"  - SMTP_EMAIL loaded: {bool(SMTP_EMAIL)}")
print(f"  - SMTP_PASSWORD loaded: {bool(SMTP_PASSWORD)}")
print(f"  - NOTIFICATION_EMAILS: {NOTIFICATION_EMAILS}")

# Validate email configuration
if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFICATION_EMAILS:
    print("\n[ERROR] Email credentials NOT fully configured!")
    print(f"  Missing: {', '.join([x for x, v in [('SMTP_EMAIL', SMTP_EMAIL), ('SMTP_PASSWORD', SMTP_PASSWORD), ('NOTIFICATION_EMAILS', NOTIFICATION_EMAILS)] if not v])}")
    print("\n[HELP] Please ensure your .env file contains:")
    print("  SMTP_EMAIL=mukherjeesagnik2@gmail.com")
    print("  SMTP_PASSWORD=your-16-char-app-password")
    print("  NOTIFICATION_EMAIL=email1@gmail.com,email2@gmail.com")
    print("\nOr run from the ping-bot-net directory where .env is located!")

# ==================== SCHEDULER SETTINGS ====================

# Schedule interval (in hours)
SCHEDULE_INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "3"))  # Default: every 3 hours

# Scheduler timezone
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")

# Database cleanup interval (in hours)
DB_CLEANUP_INTERVAL_HOURS = 201  # Run cleanup every 201 hours

# Retain data for N days
DATA_RETENTION_DAYS = 30

# Enable/disable scheduler at startup
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(task_data_path, "ping_bot.log")

print(f"\n[Config] Scheduler: {('ENABLED' if ENABLE_SCHEDULER else 'DISABLED')} (interval: {SCHEDULE_INTERVAL_HOURS}h)")