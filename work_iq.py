"""
Work IQ Integration — Microsoft's intelligence layer
Provides workplace context: people, meetings, relationships
Required for Agents League Hackathon (Microsoft IQ layer)
"""
import requests
from config import Config
from logger import get_logger

logger = get_logger("work_iq")


def get_people_context(names: list) -> dict:
    """
    Fetch workplace context for meeting participants using Work IQ.
    Falls back gracefully if Work IQ is not configured.
    """
    if not Config.WORK_IQ_ENDPOINT or not Config.WORK_IQ_API_KEY:
        logger.info("Work IQ not configured — using basic context")
        return _build_basic_context(names)

    try:
        headers = {
            "Authorization": f"Bearer {Config.WORK_IQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"participants": names}
        r = requests.post(
            f"{Config.WORK_IQ_ENDPOINT}/v1/people/context",
            headers=headers,
            json=payload,
            timeout=10
        )
        if r.status_code == 200:
            context = r.json()
            logger.info(f"Work IQ context fetched for {len(names)} participants")
            return context
        else:
            logger.warning(f"Work IQ returned {r.status_code} — using basic context")
            return _build_basic_context(names)

    except Exception as e:
        logger.warning(f"Work IQ unavailable: {e} — using basic context")
        return _build_basic_context(names)


def enrich_action_items(action_items: list, work_iq_context: dict) -> list:
    """
    Enrich action items with Work IQ people context.
    Adds email, role, and team info to each owner.
    """
    people = work_iq_context.get("people", {})

    enriched = []
    for item in action_items:
        owner = item.get("owner", "")
        person_info = people.get(owner, {})

        enriched_item = {
            **item,
            "owner_email": person_info.get("email", f"{owner.lower().replace(' ', '.')}@company.com"),
            "owner_role": person_info.get("role", "Team Member"),
            "owner_team": person_info.get("team", "Engineering"),
        }
        enriched.append(enriched_item)

    logger.info(f"Enriched {len(enriched)} action items with Work IQ context")
    return enriched


def build_work_iq_prompt_context(names: list) -> str:
    """
    Build a context string to inject into the agent system prompt.
    This is the core Work IQ integration for Azure AI Foundry.
    """
    context = get_people_context(names)
    people = context.get("people", {})

    if not people:
        return ""

    lines = ["Work IQ Context — Participant Information:"]
    for name, info in people.items():
        lines.append(
            f"- {name}: {info.get('role', 'Team Member')} "
            f"in {info.get('team', 'Engineering')} team, "
            f"email: {info.get('email', 'unknown')}"
        )

    return "\n".join(lines)


def _build_basic_context(names: list) -> dict:
    """Fallback basic context when Work IQ is not available."""
    people = {}
    custom_mappings = {
        "akshat": "akshat.mishra@bhumiitech.com",
        "akshat mishra": "akshat.mishra@bhumiitech.com"
    }
    for name in names:
        clean = name.strip()
        lower_name = clean.lower()
        if lower_name in custom_mappings:
            email = custom_mappings[lower_name]
        else:
            email = lower_name.replace(" ", ".") + "@company.com"
            
        people[clean] = {
            "email": email,
            "role": "Team Member",
            "team": "Engineering"
        }
    return {"people": people, "source": "basic_fallback"}
