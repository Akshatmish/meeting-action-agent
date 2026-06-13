"""
MeetingActionAgent — Main Orchestrator
Agents League Hackathon 2026 — Enterprise Agents Track
Powered by: Azure AI Foundry + Work IQ + GitHub + Notion + SendGrid
"""
from agent import analyze_transcript
from github_integration import create_all_issues
from notion_integration import create_all_tasks
from email_sender import send_all_emails
from jira_integration import create_all_jira_tasks
from config import Config
from logger import get_logger

logger = get_logger("main")

BANNER = """
======================================================
         MeetingActionAgent
         Azure AI Foundry + Work IQ
         Agents League Hackathon 2026
======================================================
"""


def run(transcript: str, attendee_emails: list, organizer_name: str = None, organizer_email: str = None) -> dict:
    print(BANNER)

    # Validate all keys first
    Config.validate()

    logger.info("Starting MeetingActionAgent pipeline...")
    logger.info(f"Attendees to email: {attendee_emails}")

    # STEP 1: AI Analysis (Azure AI Foundry + Work IQ)
    logger.info("-" * 50)
    logger.info("STEP 1: Analyzing transcript with Azure AI + Work IQ")
    result = analyze_transcript(transcript)

    participants = result.get("participants", [])
    action_items = result.get("action_items", [])
    decisions = result.get("decisions", [])
    summary = result.get("summary", "")

    logger.info(f"Summary: {summary[:80]}...")
    logger.info(f"Action items: {len(action_items)}")
    logger.info(f"Decisions: {len(decisions)}")

    # STEP 2: GitHub Issues
    logger.info("-" * 50)
    if Config.GITHUB_PAT:
        logger.info("STEP 2: Creating GitHub Issues...")
        github_results = create_all_issues(action_items)
    else:
        logger.info("STEP 2: Skipping GitHub (GITHUB_PAT not set)")
        github_results = []

    # STEP 3: Notion Tasks + Summary Page
    logger.info("-" * 50)
    if Config.NOTION_TOKEN and Config.NOTION_DATABASE_ID:
        logger.info("STEP 3: Creating Notion tasks + summary page...")
        notion_urls = create_all_tasks(
            action_items=action_items,
            summary=summary,
            decisions=decisions,
            participants=participants,
            organizer_name=organizer_name,
            organizer_email=organizer_email
        )
    else:
        logger.info("STEP 3: Skipping Notion (NOTION_TOKEN or NOTION_DATABASE_ID not set)")
        notion_urls = []

    # STEP 4: Jira Tickets
    logger.info("-" * 50)
    if Config.JIRA_API_TOKEN:
        logger.info("STEP 4: Creating Jira tickets...")
        jira_results = create_all_jira_tasks(action_items)
    else:
        logger.info("STEP 4: Skipping Jira (JIRA_API_TOKEN not set)")
        jira_results = []

    # STEP 5: Email Summary
    logger.info("-" * 50)
    if Config.SENDGRID_API_KEY:
        logger.info("STEP 5: Sending email summaries...")
        # Get owner emails from enriched action items
        owner_emails = list(set([
            item.get("owner_email", "")
            for item in action_items
            if item.get("owner_email", "")
        ]))

        all_emails = list(set(attendee_emails + owner_emails))
        send_all_emails(
            emails=all_emails,
            summary=summary,
            action_items=action_items,
            decisions=decisions,
            organizer_name=organizer_name,
            organizer_email=organizer_email
        )
    else:
        logger.info("STEP 5: Skipping Email (SENDGRID_API_KEY not set)")
        all_emails = []

    # Final report
    logger.info("-" * 50)
    logger.info("[OK] MeetingActionAgent pipeline complete!")
    logger.info(f"   GitHub issues created : {len(github_results)}")
    logger.info(f"   Notion pages created  : {len(notion_urls)}")
    logger.info(f"   Jira tickets created  : {len(jira_results)}")
    logger.info(f"   Emails sent           : {len(all_emails)}")
    logger.info("-" * 50)

    return {
        "summary": summary,
        "action_items": action_items,
        "decisions": decisions,
        "github_issues": github_results,
        "notion_pages": notion_urls,
        "jira_tickets": jira_results,
        "emails_sent": all_emails
    }



if __name__ == "__main__":
    # Sample transcript for testing
    SAMPLE_TRANSCRIPT = """
    Meeting: Product Sprint Planning
    Date: June 12, 2026
    Attendees: Akshat, Priya, Rahul

    Akshat: Good morning everyone. Let us start with the sprint review.
    We have a critical login bug that is affecting all enterprise users.
    Rahul, can you take ownership of this and fix it by tomorrow EOD?

    Rahul: Yes I will pick that up. I also noticed the API rate limiting
    is not configured correctly. It needs to be fixed before the next
    release otherwise we will hit production issues.

    Priya: I will set up the CI/CD pipeline this week. Should be done
    by Friday. Also the README documentation needs to be updated to
    reflect the new deployment process.

    Akshat: Good points. Let us also make sure we write unit tests for
    the new authentication module. Priya can you handle that along with
    the pipeline?

    Priya: Sure, I can do both by end of week.

    Akshat: Rahul, after the login bug, please also review the database
    indexing. Our queries are slow in production.

    Rahul: Noted. I will prioritize the login bug first then move to
    database optimization next week.

    Akshat: Perfect. We also decided today to move our deployment to
    Kubernetes by end of this quarter. Everyone is aligned on this.
    """

    run(
        transcript=SAMPLE_TRANSCRIPT,
        attendee_emails=["akshat@company.com"]
    )
