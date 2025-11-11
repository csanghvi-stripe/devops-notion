import os
import hmac
import hashlib
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from notion_client import Client as NotionClient
from slack_sdk import WebClient as SlackClient
from langchain_community.agent_toolkits import GitHubToolkit, SlackToolkit
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from langchain.prompts import PromptTemplate

load_dotenv()

app = Flask(__name__)

# Initialize clients with proper error handling
try:
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))
    slack = SlackClient(token=os.getenv("SLACK_USER_TOKEN"))
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
except Exception as e:
    print(f"Error initializing clients: {e}")

# Initialize GitHub
github = GitHubAPIWrapper()
github_toolkit = GitHubToolkit.from_github_api_wrapper(github)
slack_toolkit = SlackToolkit()

# Custom Tools
@tool
def update_notion_task(task_id: str, new_status: str, pr_link: str = None) -> str:
    """Update a Notion task with new status and optional PR link."""
    try:
        properties = {"Status": {"select": {"name": new_status}}}
        if pr_link:
            properties["PR Link"] = {"url": pr_link}
        notion.pages.update(page_id=task_id, properties=properties)
        return f"Task {task_id} updated to {new_status}"
    except Exception as e:
        return f"Error updating task: {str(e)}"

@tool
def notify_slack(channel: str, message: str, pr_url: str) -> str:
    """Send a notification to Slack with PR details."""
    try:
        slack.chat_postMessage(channel=channel, text=f"{message}\nReview PR: {pr_url}")
        return "Notification sent to Slack"
    except Exception as e:
        return f"Error sending Slack message: {str(e)}"

@tool
def ai_review_pr(repo: str, pr_number: int) -> str:
    """Generate an AI-powered review summary of a pull request."""
    try:
        from github import Github
        gh = Github(os.getenv("GITHUB_TOKEN"))
        pr = gh.get_repo(repo).get_pull(pr_number)
        files = pr.get_files()
        
        # Create a summary of changed files
        file_summary = "\n".join([f"- {f.filename}: {f.changes} changes" for f in files])
        summary = llm.invoke(f"Summarize these PR changes:\n{file_summary}").content
        return summary
    except Exception as e:
        return f"Error reviewing PR: {str(e)}"

tools = [update_notion_task, notify_slack, ai_review_pr] + github_toolkit.get_tools() + slack_toolkit.get_tools()

prompt = PromptTemplate.from_template(
    "On PR open: Get task_id from PR body, update Notion to 'Verify', AI review, notify Slack. On approval: Merge PR, update to 'Done'."
)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook events."""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Hub-Signature-256')
        payload = request.data
        secret = os.getenv("WEBHOOK_SECRET", "").encode()
        
        if not secret:
            return jsonify({"error": "WEBHOOK_SECRET not configured"}), 500
        
        hash_val = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(f'sha256={hash_val}', signature):
            return jsonify({"error": "Invalid signature"}), 403

        data = request.json
        
        # Handle PR opened event
        if data.get('action') == 'opened' and 'pull_request' in data:
            pr = data['pull_request']
            
            # Safely extract task_id from PR body
            task_id = None
            if pr.get('body') and "Notion Task: " in pr['body']:
                task_id = pr['body'].split("Notion Task: ")[1].split()[0]
            
            if task_id:
                input_data = {
                    "task_id": task_id,
                    "pr_url": pr['html_url'],
                    "channel": "#pr-reviews",
                    "repo": data['repository']['full_name'],
                    "pr_number": pr['number']
                }
                agent.invoke({"input": prompt.format(**input_data)})
        
        return jsonify({"status": "processed"}), 200
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=False)
