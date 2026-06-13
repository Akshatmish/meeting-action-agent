"""
Notion Integration
Creates task pages and meeting summary in Notion database
"""
import requests
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config
from logger import get_logger

logger = get_logger("notion")

def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {Config.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

PRIORITY_COLORS = {
    "high": "red",
    "medium": "yellow",
    "low": "green"
}

_cached_properties = None

def get_database_properties() -> set:
    global _cached_properties
    if _cached_properties is not None:
        return _cached_properties
    try:
        r = requests.get(
            f"https://api.notion.com/v1/databases/{Config.NOTION_DATABASE_ID}",
            headers=get_headers(),
            timeout=10
        )
        if r.status_code == 200:
            properties = r.json().get("properties", {})
            _cached_properties = set(properties.keys())
            logger.info(f"Retrieved Notion database properties: {_cached_properties}")
            return _cached_properties
        else:
            logger.warning(f"Could not retrieve Notion database schema (status {r.status_code}): {r.text}")
    except Exception as e:
        logger.warning(f"Error retrieving Notion database schema: {e}")
    
    # Fallback to assuming all standard properties exist if request fails
    return {"Task", "Owner", "Deadline", "Priority", "Status", "Category", "Meeting Date"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
def create_notion_task(task, owner, deadline, priority, category="technical", owner_email=""):
    today = datetime.now().strftime("%Y-%m-%d")
    valid_props = get_database_properties()

    properties = {}
    
    # Map title/task description
    if "Task" in valid_props:
        properties["Task"] = {
            "title": [{"text": {"content": task}}]
        }
    if "Text" in valid_props:
        properties["Text"] = {
            "rich_text": [{"text": {"content": task}}]
        }
        
    # Map other fields if they exist in user's database
    if "Owner" in valid_props:
        properties["Owner"] = {
            "rich_text": [{"text": {"content": f"{owner} ({owner_email})" if owner_email else owner}}]
        }
    if "Deadline" in valid_props:
        properties["Deadline"] = {
            "rich_text": [{"text": {"content": deadline}}]
        }
    if "Priority" in valid_props:
        properties["Priority"] = {
            "select": {
                "name": priority.capitalize(),
                "color": PRIORITY_COLORS.get(priority.lower(), "default")
            }
        }
    if "Status" in valid_props:
        # Check type of property to prevent error. We assume select.
        properties["Status"] = {
            "select": {"name": "To Do", "color": "blue"}
        }
    if "Category" in valid_props:
        properties["Category"] = {
            "select": {"name": category.capitalize(), "color": "purple"}
        }
    if "Meeting Date" in valid_props:
        properties["Meeting Date"] = {
            "rich_text": [{"text": {"content": today}}]
        }

    data = {
        "parent": {"database_id": Config.NOTION_DATABASE_ID},
        "properties": properties
    }

    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=get_headers(),
        json=data,
        timeout=10
    )

    if r.status_code == 200:
        url = r.json()["url"]
        logger.info(f"Notion task created: {task}")
        return url
    else:
        logger.error(f"Notion error {r.status_code}: {r.text}")
        raise Exception(f"Notion API failed: {r.status_code}")


def create_summary_page(summary: str, decisions: list, participants: list, organizer_name: str = "", organizer_email: str = "") -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    valid_props = get_database_properties()

    decisions_text = "\n".join([f"• {d}" for d in decisions]) if decisions else "No decisions recorded"
    participants_text = ", ".join(participants) if participants else "Unknown"

    children = []
    
    # Prepend organizer block if available
    if organizer_name:
        org_desc = f"Organized by: {organizer_name}"
        if organizer_email:
            org_desc += f" ({organizer_email})"
        children.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": org_desc}}],
                "icon": {"emoji": "👤"},
                "color": "blue_background"
            }
        })

    children.extend([
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "Meeting Summary"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": summary}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "Participants"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": participants_text}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "Key Decisions"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": decisions_text}}]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {
                    "content": "Auto-generated by MeetingActionAgent 🤖 | Powered by Azure AI Foundry + Work IQ"
                }}]
            }
        }
    ])

    properties = {}
    if "Task" in valid_props:
        properties["Task"] = {
            "title": [{"text": {"content": f"📋 Meeting Summary — {today}"}}]
        }
    if "Status" in valid_props:
        properties["Status"] = {
            "select": {"name": "Summary", "color": "purple"}
        }
    if "Meeting Date" in valid_props:
        properties["Meeting Date"] = {
            "rich_text": [{"text": {"content": today}}]
        }

    data = {
        "parent": {"database_id": Config.NOTION_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=get_headers(),
        json=data,
        timeout=10
    )

    if r.status_code == 200:
        url = r.json()["url"]
        logger.info(f"Notion summary page created: {url}")
        return url
    else:
        logger.error(f"Notion summary error {r.status_code}: {r.text}")
        return ""


def create_all_tasks(action_items: list, summary: str, decisions: list = [], participants: list = [], organizer_name: str = "", organizer_email: str = "") -> list:
    urls = []

    # Create individual task pages
    for item in action_items:
        try:
            url = create_notion_task(
                task=item["task"],
                owner=item["owner"],
                deadline=item["deadline"],
                priority=item["priority"],
                category=item.get("category", "technical"),
                owner_email=item.get("owner_email", "")
            )
            urls.append(url)
        except Exception as e:
            logger.error(f"Notion task failed for '{item['task']}': {e}")

    # Create summary page
    try:
        summary_url = create_summary_page(
            summary=summary,
            decisions=decisions,
            participants=participants,
            organizer_name=organizer_name,
            organizer_email=organizer_email
        )
        if summary_url:
            urls.append(summary_url)
    except Exception as e:
        logger.error(f"Notion summary page failed: {e}")

    logger.info(f"Notion: {len(urls)} pages created")
    return urls
