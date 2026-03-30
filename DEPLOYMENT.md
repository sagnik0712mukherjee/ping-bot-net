# 🚀 Deployment Guide - Pritam News Alerts Bot

This guide walks you through deploying **Pritam News Alerts Bot** to GitHub Actions for fully automated, free execution in the cloud.

---

## **Prerequisites**
- ✅ GitHub account (you have this)
- ✅ GitHub repo with this code pushed
- ✅ API keys (already in settings.py)

---

## **Step-by-Step Setup**

### **Step 1: Push Code to GitHub**

If not already done:

```bash
cd /path/to/ping-bot-net

# Initialize git (skip if already done)
git init
git add .
git commit -m "Initial commit: Pritam News Alerts Bot"

# Add your GitHub repo as remote
git remote add origin https://github.com/YOUR_USERNAME/ping-bot-net.git
git branch -M main
git push -u origin main

# Or if using existing repo:
git push origin main
```

✅ **Verify:** Go to `https://github.com/YOUR_USERNAME/ping-bot-net` and see your code there.

---

### **Step 2: Add GitHub Secrets (API Keys)**

GitHub Actions needs your sensitive API keys. We'll store them securely as "Secrets".

**In your GitHub repo page:**

1. Click **Settings** (top navigation)
2. Go to **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Add these 3 secrets:**

| Secret Name | Value | From |
|------------|-------|------|
| `OPENAI_API_KEY` | Your OpenAI API key | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `GMAIL_APP_PASSWORD` | Your Gmail app password* | (See below) |
| `NEWSAPI_KEY` | Your NewsAPI key | Already in `settings.py` → copy it here too** |

**\* Gmail App Password Setup:**
- Go to [myaccount.google.com](https://myaccount.google.com)
- Security → 2-Step Verification (enable if not done)
- App passwords → Select "Mail" & "Windows Computer"
- Copy the 16-char password
- Add as `GMAIL_APP_PASSWORD` secret

**\*\* Optional:** NewsAPI key is in `settings.py`, but GitHub Actions can also override it via secret.

---

### **Step 3: Update Workflow to Use Secrets** (Already Done! ✅)

The workflow file (`.github/workflows/pritam-monitor.yml`) already references secrets:

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

### **Step 4: Monitor Execution**

#### **View Live Logs:**

1. Go to **Actions** tab in your GitHub repo
2. Click the latest workflow run (top one)
3. Click **monitor** job
4. Expand each step to see logs in real-time

✅ **Example:** You'll see something like:
```
2026-03-31 19:23:06 [INFO] pritam_monitor: ============================================================
2026-03-31 19:23:06 [INFO] pritam_monitor: Pritam Monitor — Starting run
[Google Alerts] 2 articles fetched.
[Twitter] 5 tweets fetched.
[AI Filter] ✅ 3/7 articles passed.
[Email] ✅ Sent to 2 recipient(s).
```

#### **Check Execution History:**

- **Actions** tab shows all past runs
- Click any run to see full details
- Logs stay for **30 days** (configurable)

---

### **Step 5: Download & View Full Logs**

After each run, logs are saved as **Artifacts**.

**To download:**

1. Go to **Actions** → latest run
2. Scroll down to **Artifacts** section
3. Download `pritam-monitor-logs-*.txt`
4. View in any text editor

✅ **Logs include:** All fetch operations, AI filter decisions, email status, timestamps

---

### **Step 6: Monitor Status & Health**

#### **Status Badge (in README):**

The workflow auto-generates a status badge. Add to your `README.md`:

```markdown
![Pritam Monitor Status](https://github.com/YOUR_USERNAME/ping-bot-net/actions/workflows/pritam-monitor.yml/badge.svg)
```

Shows: 🟢 **Passing** or 🔴 **Failing**

#### **Track Execution Count:**

Each run is numbered:
- Run #1, Run #2, Run #3... (visible in Actions tab)
- Shows: Status (✅/❌), timestamp, logs

#### **Persistent State:**

The `seen_urls.json` file is automatically:
- ✅ Committed back to the repo after each run
- ✅ Prevents duplicate emails across runs
- ✅ Preserved in git history

---

## **Scheduling**

### **Current Schedule (in workflow):**
```yaml
schedule:
    - cron: '0 * * * *'  # Every hour at :00
```

**To change schedule:**

Edit `.github/workflows/pritam-monitor.yml`:

| Schedule | Cron |
|----------|------|
| Every 30 mins | `'*/30 * * * *'` |
| Every 1 hour | `'0 * * * *'` ✅ |
| Every 4 hours | `'0 */4 * * *'` |
| Every 6 hours | `'0 */6 * * *'` |
| Daily at 9 AM IST | `'30 3 * * *'` (UTC) |

---

## **Manual Trigger**

Workflow supports manual execution:

1. Go to **Actions** tab
2. Select **🎵 Pritam Monitor Bot** workflow
3. Click **Run workflow**
4. Logs update in real-time

✅ Useful for testing before schedule starts!

---

## **Troubleshooting**

### **❌ Workflow failed?**

1. Click the failed run
2. Expand each step (red ✗ steps)
3. See error message
4. Common issues:

| Error | Fix |
|-------|-----|
| `Secret not found` | Add missing secret in Settings → Secrets |
| `Connection timeout` | API is slow/down - will retry next hour |
| `Email failed` | Check SMTP credentials in settings.py |
| `Git push failed` | Ensure `GITHUB_TOKEN` has write access |

### **❓ No emails received?**

1. Check **logs** for `[Email] ✅ Sent`
2. If not in logs → check AI filter (too strict?)
3. Check spam folder
4. Test sending manually:
   ```bash
   python3 main.py --dry-run  # Shows what would be sent
   ```

---

## **Cost Breakdown** 💰

| Service | Cost | Limit |
|---------|------|-------|
| GitHub Actions | **FREE** | 2000 min/month (plenty!) |
| OpenAI API | **Paid** (you choose) | Variable |
| Gmail SMTP | **FREE** | Unlimited |
| NewsAPI Free Tier | **FREE** | 100 req/day |
| **Total** | **Mostly FREE** | Depends on OpenAI usage |

**Per-run cost:** ~$0.01-$0.05 (OpenAI) if filtering articles

---

## **Next Steps**

1. ✅ Push code to GitHub
2. ✅ Add secrets (OPENAI_API_KEY, GMAIL_APP_PASSWORD, NEWSAPI_KEY)
3. ✅ Workflow will auto-run hourly
4. ✅ Check **Actions** tab for logs & status
5. ✅ Download artifacts for detailed logs

---

## **Monitoring Dashboard** 📊

**Quick access links:**

- 🏃 **Workflow Runs:** `https://github.com/YOUR_USERNAME/ping-bot-net/actions`
- 📊 **Latest Run:** `https://github.com/YOUR_USERNAME/ping-bot-net/actions/workflows/pritam-monitor.yml`
- 📝 **Settings/Secrets:** `https://github.com/YOUR_USERNAME/ping-bot-net/settings/secrets/actions`

---

## **Pro Tips** 🎯

1. **Use `workflow_dispatch`** to manually test before schedule starts
2. **Check logs after first run** to verify everything works
3. **Save artifacts locally** for audit/backup
4. **Monitor email delivery** - check spam folder for first email
5. **Scale easily** - no infra management needed!

---

**Questions?** Check GitHub Actions docs: https://docs.github.com/en/actions

Good luck! 🚀
