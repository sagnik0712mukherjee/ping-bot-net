# 🚀 GitHub Actions Deployment - Pritam News Alerts Bot

**Goal:** Deploy Pritam News Alerts Bot to run automatically every hour on GitHub (FREE tier).

---

## 📋 Pre-Deployment Checklist

- ✅ Do you have a GitHub account? (Yes)
- ✅ Do you have code locally? (Yes, in Desktop/Sagnik Work/Pritam/Ping - Bot/ping-bot-net)
- ✅ Do you have API keys? (Yes, in settings.py)

**Estimated time:** 15 minutes

---

## **STEP 1: Create GitHub Repository**

### Option A: New Repository (Recommended)

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `ping-bot-net` (or your choice)
   - **Description:** "Pritam News Alerts Bot - Automated news monitoring with GPT-4 filtering"
   - **Visibility:** `Private` (keep sensitive configs safe)
   - **Add .gitignore:** `Python`
   - **Add LICENSE:** `MIT` (optional)
3. Click **Create repository**

### Option B: Use Existing Repository

If you already have a repo, go to Step 2.

---

## **STEP 2: Push Code to GitHub**

**On your Mac terminal:**

```bash
# Navigate to your project
cd "/Users/sagnikmukherjee/Desktop/Sagnik Work/Pritam/Ping - Bot/ping-bot-net"

# Check if git is initialized
git status

# If NOT initialized, do this:
git init
git add .
git commit -m "🎵 Initial commit: Pritam News Alerts Bot"

# Add your GitHub repo as remote
# Replace YOUR_USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR_USERNAME/ping-bot-net.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**✅ Verify:** Go to `https://github.com/YOUR_USERNAME/ping-bot-net` and see your code there.

---

## **STEP 3: Add GitHub Secrets (API Keys)**

This stores your sensitive API keys securely. GitHub Actions will access them.

### In Browser:

1. Go to your repo: `https://github.com/YOUR_USERNAME/ping-bot-net`
2. Click **Settings** (top navigation bar)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret** (green button)

### Add Secret 1: OPENAI_API_KEY

- **Name:** `OPENAI_API_KEY`
- **Value:** Your OpenAI API key (from platform.openai.com/api-keys)
- Click **Add secret**

### **Add Secret 2: GMAIL_APP_PASSWORD (Required for Email)

**Why?** Secure way to pass Gmail credentials to GitHub Actions

1. Go to **Google Account** → myaccount.google.com
2. **Security** (left) → **2-Step Verification** (enable if not done)
3. **App passwords** (after 2-FA enabled)
4. Select: **Mail** | **Windows Computer** (just placeholders)
5. Google shows a **16-character password**
6. Copy it and add as GitHub secret:
   - **Name:** `GMAIL_APP_PASSWORD`
   - **Value:** `xxxx xxxx xxxx xxxx` (16 chars)
   - Click **Add secret**

### Add Secret 3: NEWSAPI_KEY (Optional)

- **Name:** `NEWSAPI_KEY`
- **Value:** From settings.py or newsapi.org
- Click **Add secret**

---

## **STEP 4: Verify Workflow File**

The GitHub Actions workflow file is already created at:
```
.github/workflows/pritam-news-alerts-bot.yml
```

✅ **Already pushed!** No action needed.

---

## **STEP 5: Enable GitHub Actions**

1. On your repo page, click **Actions** tab
2. You should see the workflow: **🎵 Pritam News Alerts Bot**
3. It should be visible now (already pushed)

---

## **STEP 6: Manual Test Run (IMPORTANT!)**

Before the schedule starts, test it manually.

1. Go to **Actions** tab
2. Left sidebar → Click **🎵 Pritam News Alerts Bot** workflow
3. Click **Run workflow** button (right side)
4. Select branch: `main`
5. Click **Run workflow**

**⏳ Wait 1-2 minutes for execution...**

---

## **STEP 7: View Logs in Real-Time**

1. In **Actions** tab, you'll see a new run in progress
2. Click the latest run (top one)
3. Click **monitor** job (blue bar)
4. Expand each step ⏷ to see logs:
   - ✅ Checkout code
   - ✅ Setup Python
   - ✅ Install dependencies
   - ✅ Run Pritam News Alerts Bot ← **Main step**
   - ✅ Save logs as artifact

**Expected output in logs:**

```
⏱️ Starting Pritam News Alerts Bot at 2026-03-31 19:23:06 UTC
2026-03-31 19:23:06 [INFO] pritam_monitor: ============================================================
2026-03-31 19:23:06 [INFO] pritam_monitor: Pritam News Alerts Bot — Starting run
Lookback: 2h | Keywords: 12
============================================================
[Google Alerts] 2 articles fetched.
[Twitter] 0 tweets fetched.
[Hashtags] 0 posts fetched.
... (more sources)
[AI Filter] ✅ 2/4 articles passed.
[Email] ✅ Sent to 2 recipient(s).
✅ Pritam News Alerts Bot completed at 2026-03-31 19:23:48 UTC
```

---

## **STEP 8: Check Email Received**

**In your inbox (mukherjeesagnik2@gmail.com & palashchaturvedi@gmail.com):**

✅ Look for email with subject:
```
🎵 Pritam News Alerts — Latest Buzz [Mar 31, 2026]
```

**If NOT received:**

1. Check **spam folder**
2. Check logs in step 7 for errors
3. Verify `RECIPIENT_EMAILS` in settings.py are correct
4. Re-run with: `python3 main.py --dry-run` (locally)

---

## **STEP 9: Verify Bot Functionality**

**The bot is working when you see:**

1. ✅ Logs show successful articles fetched
2. ✅ AI Filter result visible in logs
3. ✅ Email sent confirmation in logs
4. ✅ Next run happens in 1 hour (automatic)

**Note:** `seen_urls.json` stays LOCAL on your machine — persists between runs but never pushed to GitHub.

---

## **STEP 10: Automated Schedule Starts**

**What happens next:**

- ✅ Workflow runs **every 1 hour** automatically (you can see it in Actions tab)
- ✅ Each run gets a **Run #N** number (Run #1, Run #2, etc)
- ✅ Logs saved as **Artifacts** for 30 days
- ✅ No manual intervention needed!

---

## 📊 **Monitoring Dashboard Setup**

### **View Execution History:**

1. Go to repo → **Actions** tab
2. Click **🎵 Pritam News Alerts Bot** (left sidebar)
3. See all past and upcoming runs with:
   - ✅/❌ Status (green = success, red = failed)
   - ⏱️ Duration (~30-60 seconds)
   - 🕐 Timestamp (UTC)

### **Download Logs:**

1. Click any completed run
2. Scroll to **Artifacts** section
3. Download `pritam-monitor-logs-*.txt`

### **Create Status Badge:**

Add to your `README.md`:

```markdown
[![Pritam News Alerts Bot](https://img.shields.io/badge/Pritam%20News%20Alerts%20Bot-Active-brightgreen)](https://github.com/YOUR_USERNAME/ping-bot-net/actions)
```

---

## 🔄 **Changing Schedule**

**Want to run every 4 hours instead of 1 hour?**

1. Open `.github/workflows/pritam-news-alerts-bot.yml` (in your repo)
2. Find this section:
   ```yaml
   schedule:
     - cron: '0 * * * *'  # Every hour
   ```
3. Change to (examples):
   ```yaml
   '0 */4 * * *'          # Every 4 hours
   '0 */6 * * *'          # Every 6 hours
   '0 9 * * *'            # Daily at 9 AM UTC
   ```
4. Commit & push
5. Schedule automatically updates!

---

## ✅ **Deployment Complete!**

You now have:

- ✅ Bot running automatically every 1 hour (FREE!)
- ✅ All logs visible in Actions tab
- ✅ Execution count tracked (Run #1, #2, etc)
- ✅ Status badge for monitoring
- ✅ Persistent state via git (no duplicates)
- ✅ Zero cost deployment

---

## 🚨 **Troubleshooting**

### **Workflow doesn't appear in Actions tab?**

- Push `.github/workflows/pritam-monitor.yml` to repo
- Go to Actions tab and refresh

### **Secrets not working?**

- Verify secret names match exactly (case-sensitive):
  - `OPENAI_API_KEY` ✅
  - `openai_api_key` ❌

### **Workflow fails?**

1. Click the failed run
2. Click **monitor** job
3. Expand red ✗ steps
4. Read error message
5. Common fixes:
   - Missing secret → Add it
   - API rate limited → Will retry next hour
   - SMTP error → Check password & credentials

### **No emails sent?**

1. Check logs for `[Email] ✅ Sent`
2. If not there → AI filter rejected articles
3. Try lowering filter strictness or check keywords
4. Test locally: `python3 main.py --dry-run`

---

## 📞 **Next Steps**

1. ✅ Push repo to GitHub
2. ✅ Add secrets (OPENAI_API_KEY minimum)
3. ✅ Run manual test
4. ✅ Check for email
5. ✅ Verify logs in Actions tab
6. ✅ Let it run on schedule!

---

## 💡 **Pro Tips**

- 📊 Check status anytime: `https://github.com/YOUR_USERNAME/ping-bot-net/actions`
- 📝 Keep logs for audit: Save artifacts locally
- 🔐 Never commit API keys—always use secrets
- 🔄 Dedup state auto-commits (no duplicates!)
- 📧 Gmail app passwords are safer than real passwords
- 🎯 Manual runs useful for testing before schedule

---

**Done!** Your Pritam Monitor Bot is now deployed in the cloud. 🚀

Questions? Check [DEPLOYMENT.md](DEPLOYMENT.md) for more details.
