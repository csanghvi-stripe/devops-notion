# **DevOps Flow Bot**  
*Notion-Centric PR Workflow with GitHub, Slack & AI (LangChain)*  

> **One workspace. Zero context-switch. AI-powered reviews.**  
> Automates task tracking, PR notifications, AI code summaries, approvals, and merges — all centered in **Notion**.

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
devops-bot/
├── app.py                  # Main Flask + LangChain agent
├── .env.example            # Template for env vars
├── requirements.txt
├── README.md               # ← You are here
└── utils/
    └── helpers.py          # Optional: parsing, logging
```

---

## Setup Guide (For New Developers)

### 1. Clone the Repo
```bash
git clone https://github.com/Cdotsanghvi/devops-bot.git
cd devops-bot
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Copy & Fill `.env`
```bash
cp .env.example .env
```

#### `.env` Variables (Required)

```env
# === Notion ===
NOTION_TOKEN=secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
NOTION_DATABASE_ID=32characterdatabaseidhere

# === GitHub ===
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
GITHUB_REPOSITORY=Cdotsanghvi/my-awesome-app   # ← YOUR PROJECT REPO
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Optional: Personal Access Token

# === Slack ===
SLACK_USER_TOKEN=xoxp-XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# === AI ===
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# === Security ===
WEBHOOK_SECRET=your-random-32-byte-hex-string
```

> **Never commit `.env`** — add it to `.gitignore`.

---

## Step-by-Step Setup

### Step 1: Create Notion Database

1. Go to [Notion](https://notion.so)
2. Create a new database: **"Dev Tasks & PRDs"**
3. Add these properties:
   - `Name` → Title
   - `Status` → Select: `To Do`, `In Progress`, `Verify`, `Done`
   - `PR Link` → URL
   - `Assignee` → Person
   - `Slack Channel` → Text (default: `#pr-reviews`)
   - `Task ID` → Text (unique, e.g., `TASK-001`)
4. **Copy Database ID** from URL:  
   `https://www.notion.so/username/abc123...v=xyz` → `abc123...` = `NOTION_DATABASE_ID`

---

### Step 2: Create GitHub App

1. Go to: [github.com/settings/apps](https://github.com/settings/apps)
2. **New GitHub App**
   - Name: `DevOps Flow Bot`
   - Homepage: `https://github.com/Cdotsanghvi/devops-bot`
   - Webhook URL: *(fill later with ngrok)*
   - Webhook Secret: *(use `WEBHOOK_SECRET` from `.env`)*
3. **Permissions**:
   - `Pull Requests`: Read & Write
   - `Issues`: Read & Write
   - `Contents`: Read
4. **Generate Private Key** → Download `.pem`
5. **Install App** on **your project repo** (`Cdotsanghvi/my-awesome-app`)
6. Copy:
   - **App ID** → `GITHUB_APP_ID`
   - **Private Key (full PEM)** → `GITHUB_APP_PRIVATE_KEY`

---

### Step 3: Set Up Slack Bot

1. Go to: [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → "From scratch"
   - Name: `DevOps Bot`
   - Workspace: Your team
3. **OAuth & Permissions** → Scopes:
   - `chat:write`
   - `chat:write.customize`
   - `channels:read`
   - `im:write`
4. **Install App** → Copy **User OAuth Token** → `SLACK_USER_TOKEN`
5. Invite bot to `#pr-reviews`: `/invite @DevOps Bot`

---

### Step 4: Run Locally with Ngrok

```bash
# Start Flask
python app.py
```

In another terminal:
```bash
ngrok http 5000
```

Copy the **https** URL → Update in GitHub App **Webhook URL**

---

### Step 5: Add Webhook to GitHub (Project Repo)

1. In **your project repo** (`Cdotsanghvi/my-awesome-app`):
   - Settings → Webhooks → Add webhook
2. Payload URL: `https://your-ngrok-url.ngrok.io/webhook`
3. Content type: `application/json`
4. Secret: `WEBHOOK_SECRET` from `.env`
5. Events: **Pull requests**

---

## How to Use (Developer Workflow)

1. **Create Task in Notion**
   - Title: `Fix login redirect loop`
   - Task ID: `TASK-042`
   - Status: `In Progress`

2. **Open PR in GitHub**
   - In PR description:
     ```markdown
     Notion Task: TASK-042
     ```
   - Push code

3. **Bot Reacts**
   - Notion → Status: `Verify`
   - Slack → AI summary + **Approve** / **Request Changes** buttons
   - GitHub → AI comment posted

4. **Reviewer Approves in Slack**
   - Bot merges PR
   - Notion → Status: `Done`

---

## Testing the Flow

1. Create a test PR with:
   ```markdown
   Notion Task: TEST-001
   ```
2. Watch:
   - Notion update
   - Slack message
   - AI review comment

---

## Production Deployment (Optional)

| Platform | Command |
|--------|--------|
| **Render** | `render.yaml` + free web service |
| **Fly.io** | `fly deploy` |
| **Railway** | Connect GitHub repo |

---

## Security & Best Practices

- `.env` never in Git
- Use **GitHub App** (not PAT) for security
- Rotate tokens every 90 days
- Restrict Notion integration to specific databases
- Monitor rate limits (GitHub: 5000/hr, Notion: 3/sec)

---

## Troubleshooting

| Issue | Fix |
|------|-----|
| Webhook not firing | Check ngrok URL, secret, events |
| Notion not updating | Verify integration shared with DB |
| Slack bot silent | Check token scopes, invite to channel |
| AI review empty | Add `GITHUB_TOKEN` for higher rate limits |

---

## Future Enhancements

- [ ] CI/CD status in Notion dashboard
- [ ] Auto-create GitHub issues from Notion
- [ ] Time tracking sync (Toggl → Notion)
- [ ] Incident alerts (PagerDuty → Notion)

---

## Author

**@Cdotsanghvi**  
*Building smarter dev tools with AI and Notion*  
[Twitter/X](https://twitter.com/Cdotsanghvi) | [GitHub](https://github.com/Cdotsanghvi)

---

**Star this repo if it saves your team 5+ hours/week**  
Let’s make Notion the OS for engineering teams.

--- 

*Last Updated: November 10, 2025*