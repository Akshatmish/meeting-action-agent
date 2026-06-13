"""
GitHub Integration
Creates GitHub Issues for technical action items
"""
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config
from logger import get_logger

logger = get_logger("github")

PRIORITY_LABELS = {
    "high": "high-priority",
    "medium": "medium-priority",
    "low": "low-priority"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
def create_github_issue(task, owner, deadline, priority, category="technical", owner_email=""):
    headers = {
        "Authorization": f"token {Config.GITHUB_PAT}",
        "Accept": "application/vnd.github+json"
    }

    body = f"""## Meeting Action Item

| Field | Value |
|-------|-------|
| **Owner** | {owner} |
| **Email** | {owner_email or 'N/A'} |
| **Deadline** | {deadline} |
| **Priority** | {priority.upper()} |
| **Category** | {category} |

## Task Description
{task}

---
*Auto-created by [MeetingActionAgent](https://github.com/Akshatmish/meeting-action-agent) 🤖*
*Powered by Azure AI Foundry + Work IQ*"""

    labels = ["meeting-action", PRIORITY_LABELS.get(priority.lower(), "medium-priority")]
    if category:
        labels.append(category)

    data = {
        "title": f"[{priority.upper()}] {task}",
        "body": body,
        "labels": labels
    }

    r = requests.post(
        f"https://api.github.com/repos/{Config.GITHUB_REPO}/issues",
        json=data,
        headers=headers,
        timeout=10
    )

    if r.status_code == 201:
        url = r.json()["html_url"]
        number = r.json()["number"]
        logger.info(f"GitHub issue #{number} created: {url}")
        return {"url": url, "number": number}
    else:
        logger.error(f"GitHub error {r.status_code}: {r.text}")
        raise Exception(f"GitHub API failed: {r.status_code}")


def create_all_issues(action_items: list) -> list:
    results = []
    for item in action_items:
        try:
            result = create_github_issue(
                task=item["task"],
                owner=item["owner"],
                deadline=item["deadline"],
                priority=item["priority"],
                category=item.get("category", "technical"),
                owner_email=item.get("owner_email", "")
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to create issue for '{item['task']}': {e}")
    logger.info(f"GitHub: {len(results)}/{len(action_items)} issues created")
    return results
