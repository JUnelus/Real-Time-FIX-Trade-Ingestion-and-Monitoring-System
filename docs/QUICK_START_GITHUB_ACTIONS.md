# Quick Start: GitHub Actions Setup

Get the automated daily FIX producer and dashboard updates running in minutes.

## 5-Minute Setup

### Step 1: Prepare Your Repository

Ensure you have:
- Repository cloned locally
- GitHub account with push access
- All new files already added (done in previous step)

### Step 2: Verify Files Are in Place

The following files should exist:

```
.github/
├── workflows/
│   ├── daily_fix_producer.yml
│   └── update_dashboard_screenshot.yml

producer/
├── top_crypto_stocks_to_fix.py
├── ... (existing files)

requirements.txt  (updated with new dependencies)

docs/
├── GITHUB_ACTIONS_SETUP.md
├── DAILY_FIX_PRODUCER_GUIDE.md
```

### Step 3: Commit and Push

```bash
# From repository root
git add -A
git commit -m "feat: add automated daily FIX producer workflow"
git push origin main
```

### Step 4: Enable GitHub Actions

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Actions** → **General**
4. Ensure "All actions and reusable workflows" is selected
5. Click **Save**

### Step 5: Verify Workflows Appear

1. Go to **Actions** tab
2. Should see two workflows listed:
   - Daily FIX Producer - Top 5 Crypto & Stocks
   - Daily Dashboard Screenshot Update
3. Status should show "No workflow runs yet"

## Testing the Workflows

### Manual Trigger (Recommended)

**Option A: GitHub UI**

1. Go to **Actions** tab
2. Click **Daily FIX Producer**
3. Click **Run workflow** button
4. Select branch: **main**
5. Click **Run workflow**
6. Wait 2-3 minutes for completion

**Option B: GitHub CLI**

```bash
# Install GitHub CLI: https://cli.github.com

# Authenticate
gh auth login

# Run workflows
gh workflow run daily_fix_producer.yml
gh workflow run update_dashboard_screenshot.yml

# Check status
gh workflow list
gh run list
```

### View Results

After running manually:

1. Go to **Actions** tab
2. Click the workflow name
3. Click the run (should show ✅ if successful)
4. Review logs:
   - Click each step to see output
   - Look for ✅ marks for success
5. Download artifacts:
   - Scroll to **Artifacts** section
   - Click **daily-fix-messages**
   - Extract and view `daily_fix_messages.json`

## Common Success Indicators

✅ **Daily FIX Producer Workflow Should:**
- Complete in ~30 seconds
- Show "Produced FIX message" logs
- Create `daily_fix_messages.json` artifact
- Display "FIX messages generated successfully" summary

✅ **Dashboard Screenshot Workflow Should:**
- Complete in ~2 minutes
- Show PostgreSQL initialization logs
- Display "Screenshot captured successfully"
- Auto-commit updated screenshot to repository

## Troubleshooting

### Workflow Doesn't Run on Schedule

**Problem:** No automated runs at scheduled times

**Solution:**
1. Make a recent commit (workflows don't run if repo inactive 60 days)
2. Verify repository Actions are enabled
3. Check that webhooks are configured (Settings → Webhooks)

```bash
# Force enable by making a dummy commit
git commit --allow-empty -m "test: trigger actions"
git push
```

### 50% Success, 50% Failure

**Dashboard screenshot fails while producer succeeds:**

This is expected! The screenshot workflow is more resource-intensive and may fail if:
- Streamlit takes too long to start
- Docker service isn't responding
- Playwright fails to capture

**Solution:**
1. Check logs for specific error
2. Increase sleep times in workflow:
   ```yaml
   - run: sleep 15  # Increase timeout
   ```
3. Check disk space and memory availability

### No Artifacts Generated

**Problem:** daily_fix_messages.json not available

**Solution:**
1. Check step logs for Python errors
2. Verify dependencies installed:
   ```bash
   pip list | grep -E "requests|yfinance"
   ```
3. Test locally:
   ```bash
   python producer/top_crypto_stocks_to_fix.py
   ```

## Customizing Schedule

### Change Execution Time

Edit `.github/workflows/daily_fix_producer.yml`:

```yaml
on:
  schedule:
    - cron: '0 14 * * *'  # Change to 2:00 PM UTC
```

After editing:
```bash
git add .github/workflows/daily_fix_producer.yml
git commit -m "config: update FIX producer schedule to 2 PM UTC"
git push
```

### Schedule Examples

| Time | Cron Expression | Notes |
|------|-----------------|-------|
| 9:00 AM UTC | `0 9 * * *` | Every day |
| 2:00 PM UTC | `0 14 * * *` | Every day |
| Every 6 hours | `0 */6 * * *` | At minute 0 |
| Mondays only | `0 9 * * 1` | Weekly |
| 1st of month | `0 9 1 * *` | Monthly |

## Integration Checklist

- [ ] Repository pushed with workflow files
- [ ] GitHub Actions enabled in Settings
- [ ] Manual test run completed successfully
- [ ] Artifacts downloaded and verified
- [ ] Screenshot updated in repository
- [ ] README updated with new information (already done)
- [ ] Documentation reviewed

## Next Steps

1. **For Local Development:**
   - Run producer manually: `python producer/top_crypto_stocks_to_fix.py`
   - Review generated `daily_fix_messages.json`
   - Test with local Kafka if needed

2. **For Production:**
   - Set up external Kafka (if using)
   - Configure GitHub Secrets for Kafka server
   - Monitor workflow runs regularly

3. **For Monitoring:**
   - Check Actions tab weekly
   - Download and archive artifacts
   - Review logs for issues

## Support & Help

**Workflow Documentation:**
- See: `docs/GITHUB_ACTIONS_SETUP.md`

**FIX Producer Details:**
- See: `docs/DAILY_FIX_PRODUCER_GUIDE.md`

**GitHub Actions Docs:**
- https://docs.github.com/en/actions
- https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule

**Issues?**
1. Check workflow logs (Actions tab)
2. Review documentation files
3. Test locally with Python script
4. Check GitHub Actions status: https://www.githubstatus.com/

## Common Gotchas

1. **Workflows don't run if repo is inactive 60+ days**
   - Solution: Make a commit to wake it up

2. **Cron times are in UTC, not your local timezone**
   - Solution: Calculate UTC offset and adjust

3. **First run may take longer due to dependency installation**
   - This is normal; subsequent runs are faster

4. **Screenshots may be blank on first run**
   - Solution: Manual test usually succeeds; small delays help

5. **GitHub Actions minutes are limited**
   - Free tier: 2,000 minutes/month per user
   - Our workflows: ~30 seconds + ~2 minutes = 84 seconds per day = ~42 minutes/month

## Final Verification

You're all set when:

✅ Both workflows appear in Actions tab  
✅ Manual test runs successfully  
✅ Artifacts are downloadable  
✅ Scheduled runs start automatically  
✅ Dashboard screenshot updates daily  

Congratulations! Your automated daily FIX producer is now live! 🚀

