# **DevOps Flow Bot**
*Notion-Centric PR Workflow with GitHub, Slack & AI*

> **One workspace. Zero context-switch. AI-powered reviews.**
> Automates task tracking, PR notifications, AI code summaries, approvals, and merges — all centered in **Notion**.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

---

## Overview

This bot connects **Notion** (your project hub), **GitHub** (code & PRs), and **Slack** (team comms) using **LangChain** to create an intelligent, automated DevOps workflow.

### Core Flow
```
Developer pushes PR
      ↓
GitHub webhook → Flask server
      ↓
LangChain Agent:
   • Parses Notion Task ID from PR body
   • Updates Notion task → "Verify"
   • Runs AI code review (GPT-4o)
   • Posts summary + approval request in Slack
      ↓
Reviewer clicks "Approve" in Slack
      ↓
Agent merges PR → Updates Notion → "Done"
```

---

## Features

| Feature | Benefit |
|-------|--------|
| **Notion as Single Source of Truth** | PRDs, tasks, status, links — all in one place |
| **AI-Powered Code Review** | Auto-summarizes changes, flags risks |
| **Slack Approval Buttons** | One-click human-in-the-loop |
| **Bi-directional Sync** | Notion ↔ GitHub issues |
| **No Jira/Confluence Needed** | Full lightweight PM in Notion |

---

## Architecture

```
[GitHub] → Webhook → [Flask Server] → [LangChain Agent]
      ↑                    ↓
[Notion API]           [Slack API] ← [OpenAI]
```

---

## Repository Structure

```
notion-bot/
├── bot.py                  # Main Flask application with service classes
├── .env.example            # Template for environment variables
├── requirements.txt        # Python dependencies
└── README.md              # ← You are here
```

**Architecture:**
- **Service-based design**: Separate classes for Notion, GitHub, Slack, and AI operations
- **Type-safe**: Full type hints throughout the codebase
- **Production-ready**: Comprehensive logging, error handling, and health checks

---

## Setup Guide (For New Developers)

### 1. Clone the Repo
```bash
git clone https://github.com/Cdotsanghvi/notion-bot.git
cd notion-bot
```

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Note for macOS users**: Port 5000 is used by AirPlay Receiver. The bot uses port 5001 by default.

### 3. Copy & Fill `.env`
```bash
cp .env.example .env
```

#### `.env` Variables (Required)

```env
# === Notion ===
NOTION_TOKEN=secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
NOTION_DATABASE_ID=32characterdatabaseidhere

# === GitHub (Choose one authentication method) ===
# Option 1: Personal Access Token (simpler for demo)
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Option 2: GitHub App (recommended for production)
# GITHUB_APP_ID=123456
# GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"

GITHUB_REPOSITORY=username/repo-name   # Format: owner/repo (NOT full URL)

# === Slack ===
SLACK_USER_TOKEN=xoxb-XXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Bot token (starts with xoxb-)
SLACK_CHANNEL=#pr-reviews  # Optional, defaults to #pr-reviews

# === AI ===
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# === Security ===
WEBHOOK_SECRET=your-random-32-byte-hex-string  # Generate with: openssl rand -hex 32

# === Optional ===
PORT=5001  # Default: 5001 (5000 conflicts with macOS AirPlay)
```

> **Never commit `.env`** — add it to `.gitignore`.

---

## Step-by-Step Setup

### Step 1: Create Notion Database

1. Go to [Notion](https://notion.so)
2. Create a new database: **"Dev Tasks & PRDs"**
3. Add these properties:
   - `Name` → Title
   - `Status` → **Status** property type with options: `To Do`, `In Progress`, `Verify`, `Done`
   - `PR Link` → URL
   - `Assignee` → Person (optional)
   - `Task ID` → **Text** (unique, e.g., `TASK-001`, `TASK-042`)
4. **Create Notion Integration**:
   - Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click "New integration"
   - Name it "DevOps Bot"
   - Copy the **Internal Integration Token** → `NOTION_TOKEN`
5. **Share database with integration**:
   - Open your database in Notion
   - Click "•••" (top right) → "Add connections"
   - Select your "DevOps Bot" integration
6. **Copy Database ID** from URL:
   `https://www.notion.so/username/abc123def456...?v=xyz` → `abc123def456...` = `NOTION_DATABASE_ID`

---

### Step 2: Set Up GitHub Authentication

**Choose one of these options:**

#### Option A: Personal Access Token (Quickest for Demo)

1. Go to: [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it "DevOps Bot"
4. Select scopes:
   - ✅ **`repo`** (Full control - required for merging PRs)
   - ✅ `workflow` (optional, for GitHub Actions)
5. Generate and copy the token → `GITHUB_TOKEN` in `.env`

#### Option B: GitHub App (Recommended for Production)

1. Go to: [github.com/settings/apps](https://github.com/settings/apps)
2. **New GitHub App**:
   - Name: `DevOps Flow Bot`
   - Homepage: `https://github.com/YOUR-USERNAME/notion-bot`
   - Webhook URL: *(fill later with ngrok URL)*
   - Webhook Secret: *(generate with `openssl rand -hex 32`)*
3. **Repository Permissions**:
   - `Pull Requests`: **Read & Write** ✅
   - `Contents`: **Read** ✅
   - `Metadata`: **Read** (auto-selected)
4. **Generate Private Key** → Download `.pem` file
5. **Install App** on your project repository
6. In `.env`:
   - Copy App ID → `GITHUB_APP_ID`
   - Copy full PEM content → `GITHUB_APP_PRIVATE_KEY`
   - Remove or comment out `GITHUB_TOKEN`

---

### Step 3: Set Up Slack Bot

1. Go to: [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → "From scratch"
   - Name: `DevOps Bot`
   - Workspace: Your team workspace
3. **OAuth & Permissions** → Add **Bot Token Scopes**:
   - ✅ `chat:write` (Post messages)
   - ✅ `chat:write.customize` (Customize bot appearance)
   - ✅ `channels:read` (View channels)
4. **Interactivity & Shortcuts**:
   - Turn on "Interactivity"
   - Request URL: `https://your-ngrok-url.ngrok.io/slack/interactions` *(fill after ngrok setup)*
5. **Install App to Workspace**
   - Click "Install to Workspace"
   - Copy **Bot User OAuth Token** (starts with `xoxb-`) → `SLACK_USER_TOKEN`
6. **Invite bot to channel**:
   - Go to `#pr-reviews` in Slack
   - Type: `/invite @DevOps Bot`

---

### Step 4: Run Locally with Ngrok

**Terminal 1 - Start the bot:**
```bash
source venv/bin/activate  # Activate virtual environment
python3 bot.py
```

You should see:
```
INFO - Configuration validated successfully
INFO - GitHub initialized with personal access token
INFO - DevOps Bot initialized successfully
INFO - Starting DevOps Flow Bot on port 5001...
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 5001
```

Copy the **https** forwarding URL (e.g., `https://abc123.ngrok.io`)

**Update webhook URLs:**
1. **GitHub Webhook**: `https://abc123.ngrok.io/webhook`
2. **Slack Interactivity**: `https://abc123.ngrok.io/slack/interactions`

---

### Step 5: Configure GitHub Webhook

1. Go to your **project repository** (e.g., `username/my-project`)
2. Navigate to: **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL**: `https://your-ngrok-url.ngrok.io/webhook`
   - **Content type**: `application/json`
   - **Secret**: Copy `WEBHOOK_SECRET` from your `.env`
   - **Events**: Select "Let me select individual events"
     - ✅ Pull requests
     - Uncheck "Pushes"
4. Click "Add webhook"
5. Test it: Create a test PR and check "Recent Deliveries" for successful pings

---

## How to Use (Developer Workflow)

### 1. Create Task in Notion
- **Title**: `Fix login redirect loop`
- **Task ID**: `TASK-042`
- **Status**: `In Progress`

### 2. Open PR in GitHub
Include the task ID anywhere in your PR description. Supported formats:
```markdown
Notion Task: TASK-042
```
or simply:
```markdown
Fixing TASK-042
Solving TASK-042
Implements TASK-042
```

### 3. Bot Automatically:
✅ **Updates Notion**: Status changes to `Verify`, adds PR link
✅ **Generates AI Review**: GPT-4 analyzes code changes
✅ **Posts GitHub Comment**: AI review summary on the PR
✅ **Sends Slack Message**: Interactive notification with:
   - PR details (author, files changed, additions/deletions)
   - AI review summary
   - **Approve & Merge** button
   - **Request Changes** button
   - **View PR** link

### 4. Reviewer Clicks "Approve & Merge" in Slack
✅ Bot merges the PR on GitHub
✅ Updates Notion status to `Done`
✅ Sends confirmation message to Slack with merge details

---

## Testing the Flow

### Quick Test

1. **Create a test task in Notion**:
   - Task ID: `TEST-001`
   - Status: `In Progress`

2. **Create a PR** with task ID in description:
   ```markdown
   Testing the DevOps Flow Bot with TASK-001
   ```

3. **Watch the automation**:
   - ✅ Check Notion: Status should change to `Verify`
   - ✅ Check GitHub: AI review comment should appear
   - ✅ Check Slack: Interactive message with buttons
   - ✅ Click "Approve & Merge" in Slack
   - ✅ Verify PR is merged and Notion shows `Done`

### Health Check

Test if the bot is running:
```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "DevOps Flow Bot",
  "version": "1.0.0"
}
```

---

## Production Deployment

### Recommended: Railway (Easiest)

1. Fork this repository
2. Sign up at [railway.app](https://railway.app)
3. Create new project → Deploy from GitHub
4. Add environment variables from `.env`
5. Railway provides HTTPS URL automatically
6. Update GitHub webhook and Slack URLs

### Alternative: Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: devops-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: PORT
        value: 10000
```
2. Deploy from GitHub

### Alternative: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t devops-bot .
docker run -p 5001:5001 --env-file .env devops-bot
```

---

## Security & Best Practices

### Essential
- ✅ **Never commit `.env`** - Already in `.gitignore`
- ✅ **Rotate secrets** every 90 days (tokens, webhook secret)
- ✅ **Use GitHub App** instead of Personal Access Token in production
- ✅ **Restrict Notion integration** to specific databases only
- ✅ **HTTPS only** for webhooks (ngrok provides this)

### Rate Limits
| Service | Limit | Mitigation |
|---------|-------|------------|
| GitHub API | 5,000/hour (PAT) or 15,000/hour (App) | Use GitHub App authentication |
| Notion API | 3 requests/second | Built-in retry logic in SDK |
| OpenAI API | Depends on tier | Monitor usage dashboard |
| Slack API | 1 message/second per channel | Rate limited by Slack SDK |

### Monitoring

Check logs for errors:
```bash
tail -f bot.log  # If you enable file logging
```

Monitor webhook deliveries:
- GitHub: Settings → Webhooks → Recent Deliveries
- Slack: api.slack.com/apps → Your App → Event Subscriptions

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 5000 already in use** | macOS AirPlay uses port 5000. Bot uses 5001 by default. Or disable AirPlay: System Preferences → General → AirPlay Receiver |
| **GitHub 404 Not Found** | Check `GITHUB_REPOSITORY` format. Must be `owner/repo`, NOT full URL |
| **GitHub 403 Merge Error** | GitHub token needs `repo` scope (full control). Regenerate token with proper permissions |
| **Notion Status Update Fails** | Ensure you're using a **Status** property type (not Select). Bot auto-detects both types |
| **No Task ID Found** | Ensure task ID follows format `TASK-##` or `XXX-##` anywhere in PR body |
| **Slack Bot Silent** | Check: (1) Token is Bot token (`xoxb-`), (2) Bot invited to channel, (3) Scopes include `chat:write` |
| **Webhook Not Firing** | Verify: (1) ngrok URL is HTTPS, (2) Webhook secret matches `.env`, (3) "Pull requests" event selected |
| **Slack Buttons Don't Work** | Update Interactivity URL in Slack app settings to `https://your-ngrok.io/slack/interactions` |
| **AI Review Empty** | Check OpenAI API key is valid and has credits |

### Enable Debug Logging

Edit `bot.py` line 25:
```python
logging.basicConfig(level=logging.DEBUG)  # Change INFO to DEBUG
```

---

## Technical Architecture

### Service Classes

```python
Config                  # Environment validation
├── NotionService      # Database queries, page updates
├── GitHubService      # PR operations, merging, comments
├── SlackService       # Block Kit messages, interactions
├── AIReviewService    # GPT-4 code analysis
└── DevOpsBot          # Orchestration layer
```

### Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/health` | GET | Health check for monitoring |
| `/webhook` | POST | GitHub webhook receiver |
| `/slack/interactions` | POST | Slack button click handler |

### Key Features

- **Auto-discovery**: Flexible task ID extraction with regex patterns
- **Dual auth support**: GitHub PAT or App authentication
- **Type safety**: Full Python type hints for maintainability
- **Error resilience**: Comprehensive try-catch with detailed logging
- **Graceful fallbacks**: AI review failures don't break the flow

## Future Enhancements

- [ ] **CI/CD Integration**: Show build status in Notion
- [ ] **Auto-create Issues**: Generate GitHub issues from Notion tasks
- [ ] **PR Templates**: Auto-populate PR descriptions from Notion
- [ ] **Analytics Dashboard**: Track merge times, review cycles
- [ ] **Multi-repo Support**: Handle webhooks from multiple repositories
- [ ] **Custom Workflows**: Configurable status transitions
- [ ] **Jira Sync** (optional): Bi-directional sync for teams using Jira

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests (if added): `pytest`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**@Cdotsanghvi**
*Building smarter dev tools with AI and Notion*
[GitHub](https://github.com/Cdotsanghvi)

---

## Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/Cdotsanghvi/notion-bot/issues)
- 💡 **Have a feature idea?** [Start a discussion](https://github.com/Cdotsanghvi/notion-bot/discussions)
- ⭐ **Like this project?** Give it a star!

**Star this repo if it saves your team 5+ hours/week**
Let's make Notion the OS for engineering teams.

---

*Last Updated: November 11, 2025*