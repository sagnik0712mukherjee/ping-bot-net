# Ping Bot - Pritam News Monitoring Bot

A sophisticated automated monitoring bot that scans the internet every 3-4 hours for news, articles, and information about music composer **Pritam**. The bot focuses on extracting relevant updates, controversies, and negative publicity from curated sources and delivers summarized findings via multiple notification channels (WhatsApp, SMS, Email).

## 🎯 Features

- **Automated Scheduling**: Runs on a 3-4 hour interval to continuously monitor Pritam-related content
- **Multi-Source Search**: Scans across curated domains including BombayTimes, Filmfare, Zoom Entertainment, and IMDB
- **AI-Powered Summarization**: Uses CrewAI with GPT-4o-mini to generate concise, point-wise summaries
- **Controversy Detection**: Highlights controversies and negative publicity from the last 24 hours
- **Multi-Channel Notifications**: Push summaries via WhatsApp, SMS, or Email
- **Deduplication**: Prevents duplicate articles from being sent to users
- **Multi-Language Support**: Tracks keywords in English, Bengali, Hindi and other languages

## 🏗️ Architecture

```
ping-bot-net/
├── config/              # Configuration and settings
├── src/
│   ├── agents/          # CrewAI agents (search, summarize)
│   ├── tasks/           # Task definitions
│   ├── tools/           # Tools for web search
│   └── notification/    # Notification adapters
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

## 🛠️ Tech Stack

- **Framework**: CrewAI for multi-agent orchestration
- **LLM**: OpenAI GPT-4o-mini
- **Search**: DuckDuckGo API via LangChain
- **Scheduler**: APScheduler (planned)
- **Database**: SQLite (planned)
- **Notifications**: Twilio (WhatsApp/SMS), SendGrid/SMTP (Email)

## 📋 Requirements

- Python 3.8+
- OpenAI API Key (GPT-4o-mini)
- Notification service credentials (Twilio for WhatsApp/SMS, SendGrid for Email)

## 🚀 Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

## 📝 Configuration

Edit `config/settings.py` to customize:
- **Keywords**: Add or remove search keywords (supports multiple languages)
- **Domains**: Curate which domains to search
- **Search Depth**: Adjust `top_k` for result count
- **Schedule**: Configure interval (3-4 hours)

## 🔄 Workflow

1. **Search Phase**: Search agent queries pre-defined keywords across curated domains
2. **Summarization Phase**: Summarizer agent synthesizes search results into point-wise summary with source links
3. **Notification Phase**: Compiled summary is sent to subscribed users via their preferred channels

## 🎯 Current Status

✅ Base implementation complete with working agents and search functionality
🔲 Scheduler integration (planned)
🔲 Database/deduplication (planned)
🔲 Multi-user notification system (planned)
🔲 Admin dashboard (planned)

## 📧 Contact & Support

**Author**: Sagnik Mukherjee  
**GitHub**: https://github.com/sagnik0712mukherjee

For questions, issues, or feature requests, please reach out via GitHub.

---

*Note: This bot is designed to monitor public information about Pritam and deliver timely updates to authorized subscribers.*
