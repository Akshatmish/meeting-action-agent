"""
Jira Integration
Creates Jira tickets for technical action items
"""
import requests
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config
from logger import get_logger

logger = get_logger("jira")

PRIORITY_MAP = {
    "high": "High",
    "medium": "Medium",
    "low": "Low"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
def create_jira_issue(task, owner, deadline, priority, category="technical", owner_email=""):
    # Check if Jira is configured
    if not Config.JIRA_URL or not Config.JIRA_EMAIL or not Config.JIRA_API_TOKEN or not Config.JIRA_PROJECT_KEY:
        logger.warning("Jira not fully configured, skipping issue creation.")
        return None

    url = f"{Config.JIRA_URL.rstrip('/')}/rest/api/2/issue"
    auth = HTTPBasicAuth(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    description = f"""## Meeting Action Item

* **Owner:** {owner}
* **Email:** {owner_email or 'N/A'}
* **Deadline:** {deadline}
* **Priority:** {priority.upper()}
* **Category:** {category}

---
*Auto-created by MeetingActionAgent 🤖*
*Powered by Azure AI Foundry + Work IQ*"""

    payload = {
        "fields": {
            "project": {
                "key": Config.JIRA_PROJECT_KEY
            },
            "summary": f"[{priority.upper()}] {task[:100]}...",
            "description": description,
            "issuetype": {
                "name": "Task"
            }
        }
    }

    # If priority can be set, do it (usually custom field or mapping)
    # Note: Standard Jira might have different priority names or require ID, so we keep it simple.
    
    r = requests.post(
        url,
        json=payload,
        headers=headers,
        auth=auth,
        timeout=10
    )

    if r.status_code == 201:
        data = r.json()
        issue_key = data.get("key")
        # In Jira API v2, the self link or issue browser link
        issue_url = f"{Config.JIRA_URL.rstrip('/')}/browse/{issue_key}"
        logger.info(f"Jira issue {issue_key} created: {issue_url}")
        return {"url": issue_url, "key": issue_key}
    else:
        logger.error(f"Jira error {r.status_code}: {r.text}")
        raise Exception(f"Jira API failed: {r.status_code} - {r.text}")


def create_all_jira_tasks(action_items: list) -> list:
    results = []
    # If Jira credentials are not present, return empty list and log warning
    if not Config.JIRA_API_TOKEN:
        logger.info("Jira integration is not enabled (missing JIRA_API_TOKEN)")
        return results

    for item in action_items:
        try:
            result = create_jira_issue(
                task=item["task"],
                owner=item["owner"],
                deadline=item["deadline"],
                priority=item["priority"],
                category=item.get("category", "technical"),
                owner_email=item.get("owner_email", "")
            )
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Failed to create Jira ticket for '{item['task']}': {e}")
            
    logger.info(f"Jira: {len(results)}/{len(action_items)} issues created")
    return results
