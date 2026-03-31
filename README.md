# 🎵 Pritam News Alerts Bot

[![Pritam News Alerts Bot](https://img.shields.io/badge/Status-Active-brightgreen)](../../actions/workflows/pritam-news-alerts-bot.yml)

An automated monitoring bot that fetches **all latest mentions** of Pritam (the composer) from 14+ news sources, filters them using **GPT-4.1** to remove false positives, and delivers a clean HTML digest email. 

**Status:** ✅ Running on GitHub Actions (every hour, FREE tier) | 📊 [View Dashboard](../../actions/workflows/pritam-news-alerts-bot.yml) | 📧 [Email Format](examples/sample_email.html)

---

## � **QUICK START: GitHub Actions Deployment (Recommended)**

**Already deployed on GitHub Actions?** Just check your email inbox and the [Actions Dashboard](../../actions/workflows/pritam-news-alerts-bot.yml)! 

The bot runs automatically **every hour** — no setup needed. See [GITHUB_DEPLOYMENT_STEPS.md](GITHUB_DEPLOYMENT_STEPS.md) for details.

---

## �📁 Project Structure

```
pritam_bot/
├── main.py           # Entry point — run this
├── settings.py       # ALL tunables live here
├── fetchers.py       # One function per source
├── dedup.py          # Cross-run deduplication
├── emailer.py        # HTML email builder + SMTP sender
├── requirements.txt
├── seen_urls.json    # Auto-created. Tracks sent articles.
└── README.md
```

---

## ⚙️ Setup

### Local Development (Optional)

For testing locally, install dependencies and configure settings:

```bash
pip install -r requirements.txt
```

### Configuration

Edit `config/settings.py`:

**On GitHub Actions:** API keys are passed via secrets (see [GITHUB_DEPLOYMENT_STEPS.md](GITHUB_DEPLOYMENT_STEPS.md)) — automatically read as environment variables.

**Locally:** You can set environment variables or edit `settings.py` directly:
- `OPENAI_API_KEY` (required for GPT-4.1 AI filtering)
- `NEWSAPI_KEY` and `GNEWS_KEY` (get free keys below)
- `GOOGLE_ALERTS_RSS_URLS` (set up RSS feeds)
- `SMTP_USERNAME`, `SMTP_PASSWORD`, `RECIPIENT_EMAILS`

---

## 🔑 Getting Your Free API Keys

### NewsAPI (100 req/day free)
1. Go to **https://newsapi.org**
2. Click **Get API Key** (top right)
3. Sign up with email — key is shown immediately on the dashboard
4. Paste it as `NEWSAPI_KEY` in `settings.py`
5. Free tier resets every 24 hours

### GNews (100 req/day free)
1. Go to **https://gnews.io**
2. Click **Get started for free**
3. Sign up → verify email → key is on your dashboard
4. Paste it as `GNEWS_KEY` in `settings.py`
5. If you run out of requests, just register a second free account with another email

---

## 🔔 Setting Up Google Alerts RSS (Highly Recommended — No Limit, No Key)

Google Alerts is the single best source for comprehensive coverage. Here's how:

1. Go to **https://www.google.com/alerts**
2. Make sure you're signed in to a Google account
3. In the search box, type your first keyword — e.g. `"Pritam Chakraborty"`
4. Click **Show options** (below the search box)
5. Set:
   - **How often**: As-it-happens
   - **Sources**: Automatic
   - **Language**: English
   - **Region**: India (or Worldwide for more coverage)
   - **How many**: All results
   - **Deliver to**: **RSS feed** ← this is the key step
6. Click **Create Alert**
7. You'll see the alert listed. Click the RSS icon (orange feed icon) to get the URL
8. Copy that URL (looks like `https://www.google.com/alerts/feeds/XXXXX/XXXXX`)
9. Paste into `GOOGLE_ALERTS_RSS_URLS` in `settings.py`
10. Repeat for each keyword: `"Pritam"`, `"Pritam composer"`, `"Pritam controversy"`, etc.

**There is NO daily limit on Google Alerts RSS feeds.** This is effectively unlimited.

---

## 📧 Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to **https://myaccount.google.com/apppasswords**
3. Under "Select app" choose **Mail**, under "Select device" choose **Other** → name it "Pritam Bot"
4. Click **Generate** — you'll get a 16-character password
5. Paste it as `SMTP_PASSWORD` in `settings.py` (NOT your real Gmail password)

---

## 🚀 Running the Bot

```bash
# Dry run — fetch everything, AI filter, print to console, NO email sent
# Also saves email_preview.html so you can see exactly what the email looks like
python main.py --dry-run

# Run once and send email (if there are new articles)
python main.py

# Run on a loop every N hours
python main.py --schedule
```

---

## 🤖 AI Filtering

This bot uses **GPT-4.1** to intelligently filter articles and remove false positives. The AI analyzes each article to ensure it's genuinely about Pritam Chakraborty, eliminating noise from unrelated results.

To enable/disable AI filtering, toggle `AI_FILTER_ENABLED` in `settings.py`.

---

## ✅ How to Run, locally?

```
# Run on a loop every N hours (set RUN_EVERY_N_HOURS in settings.py)
python main.py --schedule

# Background process (Linux/Mac)
nohup python main.py --schedule > bot.log 2>&1 &

# Or use cron instead of --schedule:
# crontab -e  →  add:
# 0 */3 * * * cd /path/to/pritam_bot && python main.py >> bot.log 2>&1
```

---

## 📡 Sources Covered

| Source | Method | Key needed? |
|---|---|---|
| Google News RSS | RSS search | None |
| Google Alerts | RSS feeds (manual setup) | None — unlimited |
| NewsAPI | REST API | Free (100/day) |
| GNews | REST API | Free (100/day) |
| Reddit | RSS (5 subreddits) | None |
| YouTube search | Invidious API | None |
| YouTube channels | Channel RSS feeds | None |
| Times of India | Direct RSS | None |
| Filmfare | Direct RSS | None |
| Zoom TV | Google News site-scoped | None |
| Pinkvilla | Direct RSS | None |
| Bollywood Hungama | Direct RSS | None |
| NDTV Entertainment | Direct RSS | None |
| IMDB | Direct page scrape | None |
| Instagram @pritamofficial | Picuki mirror (best-effort) | None |

---

## 🔁 Deduplication

The bot tracks every sent URL in `seen_urls.json`. Even if the same article appears in 3 sources, it's only sent once, ever.

To reset (re-send everything fresh): just delete `seen_urls.json`.

---

## 👤 Author

**Sagnik Mukherjee**  
GitHub: [github.com/sagnik0712mukherjee](https://github.com/sagnik0712mukherjee)