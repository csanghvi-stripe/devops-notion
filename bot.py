"""
DevOps Flow Bot
Notion-Centric PR Workflow with GitHub, Slack & AI (LangChain)

Automates task tracking, PR notifications, AI code summaries, approvals, and merges.
"""

import os
import hmac
import hashlib
import json
import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import parse_qs

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from notion_client import Client as NotionClient
from slack_sdk import WebClient as SlackClient
from langchain_openai import ChatOpenAI
from github import Github, GithubIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)


class Config:
    """Application configuration with validation."""

    REQUIRED_ENV_VARS = [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "SLACK_USER_TOKEN",
        "OPENAI_API_KEY",
        "WEBHOOK_SECRET",
        "GITHUB_REPOSITORY"
    ]

    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_database_id = os.getenv("NOTION_DATABASE_ID")
        self.slack_token = os.getenv("SLACK_USER_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_app_id = os.getenv("GITHUB_APP_ID")
        self.github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
        self.default_slack_channel = os.getenv("SLACK_CHANNEL", "#pr-reviews")

    def validate(self):
        """Validate required environment variables."""
        missing = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Validate GitHub authentication
        if not self.github_token and not (self.github_app_id and self.github_app_private_key):
            raise ValueError("Either GITHUB_TOKEN or (GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY) required")

        logger.info("Configuration validated successfully")


class NotionService:
    """Handle all Notion operations."""

    def __init__(self, config: Config):
        self.client = NotionClient(auth=config.notion_token)
        self.database_id = config.notion_database_id

    def find_task_by_id(self, task_id: str) -> Optional[str]:
        """
        Find Notion page ID by Task ID property.

        Args:
            task_id: The task identifier (e.g., 'TASK-042')

        Returns:
            Notion page ID if found, None otherwise
        """
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Task ID",
                    "rich_text": {
                        "equals": task_id
                    }
                }
            )

            if response['results']:
                page_id = response['results'][0]['id']
                logger.info(f"Found Notion page {page_id} for task {task_id}")
                return page_id
            else:
                logger.warning(f"No Notion page found for task {task_id}")
                return None

        except Exception as e:
            logger.error(f"Error finding Notion task {task_id}: {e}")
            return None

    def update_task(self, page_id: str, status: str, pr_link: Optional[str] = None) -> bool:
        """
        Update Notion task with new status and optional PR link.

        Args:
            page_id: Notion page ID
            status: New status value
            pr_link: Optional PR URL

        Returns:
            True if successful, False otherwise
        """
        try:
            properties = {
                "Status": {
                    "select": {
                        "name": status
                    }
                }
            }

            if pr_link:
                properties["PR Link"] = {
                    "url": pr_link
                }

            self.client.pages.update(page_id=page_id, properties=properties)
            logger.info(f"Updated Notion page {page_id} to status '{status}'")
            return True

        except Exception as e:
            logger.error(f"Error updating Notion page {page_id}: {e}")
            return False


class GitHubService:
    """Handle all GitHub operations."""

    def __init__(self, config: Config):
        self.config = config

        # Initialize GitHub client with appropriate authentication
        if config.github_token:
            self.client = Github(config.github_token)
            logger.info("GitHub initialized with personal access token")
        elif config.github_app_id and config.github_app_private_key:
            # Use GitHub App authentication
            integration = GithubIntegration(
                config.github_app_id,
                config.github_app_private_key
            )
            # Get installation token for the repository
            installation = integration.get_installations()[0]
            token = integration.get_access_token(installation.id).token
            self.client = Github(token)
            logger.info("GitHub initialized with App authentication")

        self.repo = self.client.get_repo(config.github_repository)

    def get_pr_details(self, pr_number: int) -> Dict[str, Any]:
        """
        Get PR details including files and metadata.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary with PR details
        """
        try:
            pr = self.repo.get_pull(pr_number)
            files = pr.get_files()

            file_changes = []
            total_additions = 0
            total_deletions = 0

            for file in files:
                file_changes.append({
                    'filename': file.filename,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'status': file.status,
                    'patch': file.patch if hasattr(file, 'patch') else None
                })
                total_additions += file.additions
                total_deletions += file.deletions

            return {
                'title': pr.title,
                'body': pr.body or '',
                'author': pr.user.login,
                'files': file_changes,
                'total_additions': total_additions,
                'total_deletions': total_deletions,
                'file_count': len(file_changes),
                'url': pr.html_url,
                'number': pr.number
            }

        except Exception as e:
            logger.error(f"Error getting PR details for #{pr_number}: {e}")
            raise

    def merge_pr(self, pr_number: int) -> bool:
        """
        Merge a pull request.

        Args:
            pr_number: Pull request number

        Returns:
            True if successful, False otherwise
        """
        try:
            pr = self.repo.get_pull(pr_number)

            if pr.mergeable:
                pr.merge(
                    commit_message=f"Merged PR #{pr_number} via DevOps Flow Bot",
                    merge_method="merge"
                )
                logger.info(f"Successfully merged PR #{pr_number}")
                return True
            else:
                logger.warning(f"PR #{pr_number} is not mergeable")
                return False

        except Exception as e:
            logger.error(f"Error merging PR #{pr_number}: {e}")
            return False

    def post_comment(self, pr_number: int, comment: str) -> bool:
        """
        Post a comment on a PR.

        Args:
            pr_number: Pull request number
            comment: Comment text

        Returns:
            True if successful, False otherwise
        """
        try:
            pr = self.repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            logger.info(f"Posted comment on PR #{pr_number}")
            return True

        except Exception as e:
            logger.error(f"Error posting comment on PR #{pr_number}: {e}")
            return False


class SlackService:
    """Handle all Slack operations."""

    def __init__(self, config: Config):
        self.client = SlackClient(token=config.slack_token)
        self.default_channel = config.default_slack_channel

    def send_pr_review_request(
        self,
        channel: str,
        pr_details: Dict[str, Any],
        ai_summary: str,
        task_id: str,
        notion_page_id: str
    ) -> Optional[str]:
        """
        Send interactive PR review request to Slack with approval buttons.

        Args:
            channel: Slack channel name
            pr_details: PR details dictionary
            ai_summary: AI-generated review summary
            task_id: Notion task ID
            notion_page_id: Notion page ID

        Returns:
            Message timestamp if successful, None otherwise
        """
        try:
            # Build Block Kit message with interactive buttons
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔔 PR Review Request: {pr_details['title']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Author:*\n{pr_details['author']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Task ID:*\n{task_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Files Changed:*\n{pr_details['file_count']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Changes:*\n+{pr_details['total_additions']} -{pr_details['total_deletions']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Review Summary:*\n{ai_summary}"
                    }
                },
                {
                    "type": "actions",
                    "block_id": "pr_review_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve & Merge"
                            },
                            "style": "primary",
                            "action_id": "approve_pr",
                            "value": json.dumps({
                                "pr_number": pr_details['number'],
                                "task_id": task_id,
                                "notion_page_id": notion_page_id,
                                "repo": pr_details.get('repo')
                            })
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Request Changes"
                            },
                            "style": "danger",
                            "action_id": "request_changes",
                            "value": json.dumps({
                                "pr_number": pr_details['number'],
                                "pr_url": pr_details['url']
                            })
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 View PR"
                            },
                            "url": pr_details['url'],
                            "action_id": "view_pr"
                        }
                    ]
                }
            ]

            response = self.client.chat_postMessage(
                channel=channel,
                text=f"PR Review Request: {pr_details['title']}",
                blocks=blocks
            )

            logger.info(f"Sent PR review request to {channel}")
            return response['ts']

        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return None

    def update_message(self, channel: str, ts: str, text: str) -> bool:
        """
        Update a Slack message.

        Args:
            channel: Slack channel ID
            ts: Message timestamp
            text: New message text

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text
            )
            return True
        except Exception as e:
            logger.error(f"Error updating Slack message: {e}")
            return False


class AIReviewService:
    """Handle AI-powered code reviews using LangChain."""

    def __init__(self, config: Config):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=config.openai_api_key
        )

    def generate_review(self, pr_details: Dict[str, Any]) -> str:
        """
        Generate AI review summary for a PR.

        Args:
            pr_details: PR details dictionary

        Returns:
            AI-generated review summary
        """
        try:
            # Build comprehensive prompt for AI review
            file_list = "\n".join([
                f"- `{f['filename']}`: {f['status']} (+{f['additions']}/-{f['deletions']})"
                for f in pr_details['files'][:10]  # Limit to first 10 files
            ])

            if pr_details['file_count'] > 10:
                file_list += f"\n... and {pr_details['file_count'] - 10} more files"

            prompt = f"""Review this pull request and provide a concise summary:

**PR Title:** {pr_details['title']}
**Author:** {pr_details['author']}
**Description:** {pr_details['body'][:500] if pr_details['body'] else 'No description provided'}

**Files Changed ({pr_details['file_count']}):**
{file_list}

**Total Changes:** +{pr_details['total_additions']} additions, -{pr_details['total_deletions']} deletions

Please provide:
1. A brief summary of what this PR does (2-3 sentences)
2. Any potential concerns or things to review carefully
3. Overall assessment (Low/Medium/High complexity)

Keep the response concise and actionable."""

            response = self.llm.invoke(prompt)
            summary = response.content

            logger.info(f"Generated AI review for PR #{pr_details['number']}")
            return summary

        except Exception as e:
            logger.error(f"Error generating AI review: {e}")
            return "⚠️ AI review unavailable. Please review manually."


class DevOpsBot:
    """Main bot orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self.notion = NotionService(config)
        self.github = GitHubService(config)
        self.slack = SlackService(config)
        self.ai_review = AIReviewService(config)

    def extract_task_id(self, pr_body: str) -> Optional[str]:
        """
        Extract task ID from PR body.

        Args:
            pr_body: PR description text

        Returns:
            Task ID if found, None otherwise
        """
        if not pr_body:
            return None

        # Match patterns like "Notion Task: TASK-042" or "Task: TASK-001"
        patterns = [
            r'Notion Task:\s*([A-Z]+-\d+)',
            r'Task:\s*([A-Z]+-\d+)',
            r'Task ID:\s*([A-Z]+-\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def handle_pr_opened(self, pr_data: Dict[str, Any], repo_name: str) -> Dict[str, str]:
        """
        Handle PR opened event: Update Notion, generate AI review, send Slack notification.

        Args:
            pr_data: PR data from webhook
            repo_name: Repository full name

        Returns:
            Result dictionary with status and message
        """
        try:
            pr_number = pr_data['number']
            pr_url = pr_data['html_url']
            pr_body = pr_data.get('body', '')

            # Extract task ID from PR body
            task_id = self.extract_task_id(pr_body)
            if not task_id:
                logger.warning(f"No task ID found in PR #{pr_number}")
                return {
                    "status": "skipped",
                    "message": "No Notion task ID found in PR description"
                }

            # Find Notion page by task ID
            notion_page_id = self.notion.find_task_by_id(task_id)
            if not notion_page_id:
                logger.warning(f"Notion page not found for task {task_id}")
                return {
                    "status": "error",
                    "message": f"Notion task {task_id} not found"
                }

            # Update Notion task to "Verify" status
            self.notion.update_task(notion_page_id, "Verify", pr_url)

            # Get PR details
            pr_details = self.github.get_pr_details(pr_number)
            pr_details['repo'] = repo_name

            # Generate AI review
            ai_summary = self.ai_review.generate_review(pr_details)

            # Post AI review as GitHub comment
            self.github.post_comment(
                pr_number,
                f"## 🤖 AI Code Review\n\n{ai_summary}\n\n---\n*Generated by DevOps Flow Bot*"
            )

            # Send Slack notification with approval buttons
            slack_channel = self.slack.default_channel
            self.slack.send_pr_review_request(
                channel=slack_channel,
                pr_details=pr_details,
                ai_summary=ai_summary,
                task_id=task_id,
                notion_page_id=notion_page_id
            )

            logger.info(f"Successfully processed PR #{pr_number} for task {task_id}")
            return {
                "status": "success",
                "message": f"PR #{pr_number} processed successfully"
            }

        except Exception as e:
            logger.error(f"Error handling PR opened event: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def handle_pr_approval(self, pr_number: int, task_id: str, notion_page_id: str) -> Dict[str, str]:
        """
        Handle PR approval: Merge PR and update Notion to "Done".

        Args:
            pr_number: PR number
            task_id: Task ID
            notion_page_id: Notion page ID

        Returns:
            Result dictionary with status and message
        """
        try:
            # Merge the PR
            merge_success = self.github.merge_pr(pr_number)

            if merge_success:
                # Update Notion task to "Done"
                self.notion.update_task(notion_page_id, "Done")

                logger.info(f"PR #{pr_number} approved and merged, task {task_id} marked as Done")
                return {
                    "status": "success",
                    "message": f"PR #{pr_number} merged and task {task_id} marked as Done"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to merge PR #{pr_number}. Check if it's mergeable."
                }

        except Exception as e:
            logger.error(f"Error handling PR approval: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Initialize configuration and bot
try:
    config = Config()
    config.validate()
    bot = DevOpsBot(config)
    logger.info("DevOps Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    bot = None


def verify_webhook_signature(request_data: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False

    secret = config.webhook_secret.encode()
    hash_val = hmac.new(secret, request_data, hashlib.sha256).hexdigest()
    expected_signature = f'sha256={hash_val}'

    return hmac.compare_digest(expected_signature, signature)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    if bot is None:
        return jsonify({"status": "unhealthy", "error": "Bot not initialized"}), 503

    return jsonify({
        "status": "healthy",
        "service": "DevOps Flow Bot",
        "version": "1.0.0"
    }), 200


@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook events."""
    if bot is None:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        # Verify webhook signature
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_webhook_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 403

        event_type = request.headers.get('X-GitHub-Event')
        data = request.json

        logger.info(f"Received GitHub webhook: {event_type}")

        # Handle pull request events
        if event_type == 'pull_request':
            action = data.get('action')

            if action == 'opened':
                pr_data = data['pull_request']
                repo_name = data['repository']['full_name']

                result = bot.handle_pr_opened(pr_data, repo_name)
                return jsonify(result), 200
            else:
                logger.info(f"Ignoring PR action: {action}")
                return jsonify({"status": "ignored", "action": action}), 200

        return jsonify({"status": "processed", "event": event_type}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/slack/interactions', methods=['POST'])
def slack_interactions():
    """Handle Slack interactive button clicks."""
    if bot is None:
        return jsonify({"error": "Bot not initialized"}), 503

    try:
        # Parse Slack payload
        payload = json.loads(request.form.get('payload'))
        action = payload['actions'][0]
        action_id = action['action_id']

        logger.info(f"Received Slack interaction: {action_id}")

        if action_id == 'approve_pr':
            # Parse action value
            action_value = json.loads(action['value'])
            pr_number = action_value['pr_number']
            task_id = action_value['task_id']
            notion_page_id = action_value['notion_page_id']

            # Handle PR approval
            result = bot.handle_pr_approval(pr_number, task_id, notion_page_id)

            # Respond to Slack
            if result['status'] == 'success':
                return jsonify({
                    "text": f"✅ {result['message']}"
                })
            else:
                return jsonify({
                    "text": f"❌ Error: {result['message']}"
                })

        elif action_id == 'request_changes':
            # Parse action value
            action_value = json.loads(action['value'])
            pr_url = action_value['pr_url']

            return jsonify({
                "text": f"👀 Please review and request changes on the PR: {pr_url}"
            })

        return jsonify({"text": "Action processed"}), 200

    except Exception as e:
        logger.error(f"Slack interaction error: {e}", exc_info=True)
        return jsonify({"text": f"Error: {str(e)}"}), 500


if __name__ == '__main__':
    if bot is None:
        logger.error("Cannot start server - bot initialization failed")
        exit(1)

    logger.info("Starting DevOps Flow Bot on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
