# 📊 Pritam News Alerts Bot - Status Dashboard

**Latest Status:** Check [Actions](../../actions) tab for real-time updates

---

## 🚀 Quick Links

| Link | Purpose |
|------|---------|
| [📊 All Runs](../../actions/workflows/pritam-news-alerts-bot.yml) | View execution history of Pritam News Alerts Bot |
| [🔑 Secrets](../../settings/secrets/actions) | Manage API keys |
| [📝 Logs](../../actions?query=workflow%3A%22Pritam+Monitor+Bot%22) | Download detailed logs |
| [⚙️ Settings](../../settings) | Configure workflow |

---

## 📈 Execution Statistics

**Schedule:** Every 1 hour (via GitHub Actions)

**Last 7 Days Performance:**

| Metric | Value |
|--------|-------|
| Total Runs | ? |
| Successful | ? |
| Failed | ? |
| Avg Duration | ~30-60 seconds |
| Success Rate | ? |

*Update these manually from Actions tab or check workflow logs*

---

## 🎯 What Gets Monitored

✅ **What Gets Monitored:**
- Google Alerts (12 keyword feeds)
- Google News (general search)
- NewsAPI (Bollywood news)
- Reddit posts
- Twitter mentions (#pritamofficial)
- Hashtag searches (#PritamNews, etc)
- Times of India, Filmfare, NDTV, Zoom, etc.

✅ **Processing:**
- 🤖 AI Filter (GPT-4) to remove false positives
- 🔄 Deduplication (no duplicate emails)
- ⏱️ Freshness check (last 2 hours)

✅ **Output:**
- 📧 Email sent to recipients
- 📋 Logs saved to artifacts (30-day retention)
- 💾 State persisted locally (seen_urls.json)

---

## 🔍 How to Monitor

### **View Live Logs:**
1. Go to **Actions** tab
2. Click latest workflow run
3. Click **monitor** job
4. Expand each step to see real-time output

### **Download Logs:**
1. Navigate to a completed run
2. Scroll to **Artifacts** section
3. Download `pritam-monitor-logs-*.txt`

### **Check Execution Count:**
- Each run gets a unique **Run #N** number
- Visible in: Actions → Workflow runs list

### **Email Status:**
- Look for `[Email] ✅ Sent to 2 recipient(s).` in logs
- If not present → AI filter rejected all articles

---

## 🛠️ Troubleshooting

### Workflow stuck/hanging?
Check the error log and see if Piped API or similar source is timing out. Solution: Already fixed with 10s timeout.

### Missing emails?
1. Check logs for filter rejection
2. Verify SMTP credentials
3. Check spam folder
4. Run `python3 main.py --dry-run` locally

### Want to test manually?
Go to **Actions** → **Run workflow** → **Run workflow** button

---

## 💡 Performance Tips

- Logs persist for 30 days (artifacts)
- State `seen_urls.json` auto-commits (no duplicates)
- Timezone: IST (converted from UTC)
- Dynamic AI prompt (auto-updates from KEYWORDS)

---

## 📊 Next: Add Detailed Metrics

To track more metrics, consider:
- [ ] Slack notifications on email send
- [ ] Response time monitoring
- [ ] Article count trends over time
- [ ] Source breakdown statistics

---

**Schedule:** Every hour (cron: `0 * * * *` UTC)
**Next Run:** Check [Actions](../../actions/workflows/pritam-news-alerts-bot.yml) tab for scheduled runs
**Status:** Real-time via [workflow logs](../../actions)
