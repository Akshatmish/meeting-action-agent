import os
from dotenv import load_dotenv

load_dotenv()

def _clean(val, default=""):
    if not val:
        return default
    val_str = str(val).strip()
    # If it contains placeholder patterns, treat it as empty/default
    placeholders = ["your_", "your-", "placeholder", "company.com", "meetingaction.ai"]
    for p in placeholders:
        if p in val_str.lower():
            return default
    return val_str

class Config:
    # Azure AI Foundry
    AZURE_API_KEY = _clean(os.getenv("AZURE_API_KEY"))
    AZURE_ENDPOINT = _clean(os.getenv("AZURE_ENDPOINT"))
    AZURE_MODEL = _clean(os.getenv("AZURE_MODEL"), "gpt-4.1-mini")
    AZURE_API_VERSION = _clean(os.getenv("AZURE_API_VERSION"), "2024-05-01-preview")

    # GitHub
    GITHUB_PAT = _clean(os.getenv("GITHUB_PAT"))
    GITHUB_REPO = _clean(os.getenv("GITHUB_REPO"), "Akshatmish/meeting-action-agent")

    # Notion
    NOTION_TOKEN = _clean(os.getenv("NOTION_TOKEN"))
    NOTION_DATABASE_ID = _clean(os.getenv("NOTION_DATABASE_ID"))

    # SendGrid
    SENDGRID_API_KEY = _clean(os.getenv("SENDGRID_API_KEY"))
    FROM_EMAIL = _clean(os.getenv("FROM_EMAIL"), "agent@meetingaction.ai")

    # Work IQ
    WORK_IQ_ENDPOINT = _clean(os.getenv("WORK_IQ_ENDPOINT"))
    WORK_IQ_API_KEY = _clean(os.getenv("WORK_IQ_API_KEY"))

    # Jira
    JIRA_URL = _clean(os.getenv("JIRA_URL"))
    JIRA_EMAIL = _clean(os.getenv("JIRA_EMAIL"))
    JIRA_API_TOKEN = _clean(os.getenv("JIRA_API_TOKEN"))
    JIRA_PROJECT_KEY = _clean(os.getenv("JIRA_PROJECT_KEY"))

    # Whisper
    AZURE_WHISPER_DEPLOYMENT = _clean(os.getenv("AZURE_WHISPER_DEPLOYMENT"))

    @classmethod
    def override(cls, data: dict):
        if not data:
            return
        if "azure_api_key" in data: cls.AZURE_API_KEY = _clean(data["azure_api_key"])
        if "azure_endpoint" in data: cls.AZURE_ENDPOINT = _clean(data["azure_endpoint"])
        if "azure_model" in data: cls.AZURE_MODEL = _clean(data["azure_model"], "gpt-4.1-mini")
        if "azure_api_version" in data: cls.AZURE_API_VERSION = _clean(data["azure_api_version"], "2024-05-01-preview")
        if "github_pat" in data: cls.GITHUB_PAT = _clean(data["github_pat"])
        if "github_repo" in data: cls.GITHUB_REPO = _clean(data["github_repo"], "Akshatmish/meeting-action-agent")
        if "notion_token" in data: cls.NOTION_TOKEN = _clean(data["notion_token"])
        if "notion_database_id" in data: cls.NOTION_DATABASE_ID = _clean(data["notion_database_id"])
        if "sendgrid_api_key" in data: cls.SENDGRID_API_KEY = _clean(data["sendgrid_api_key"])
        if "from_email" in data: cls.FROM_EMAIL = _clean(data["from_email"], "agent@meetingaction.ai")
        if "work_iq_endpoint" in data: cls.WORK_IQ_ENDPOINT = _clean(data["work_iq_endpoint"])
        if "work_iq_api_key" in data: cls.WORK_IQ_API_KEY = _clean(data["work_iq_api_key"])
        if "jira_url" in data: cls.JIRA_URL = _clean(data["jira_url"])
        if "jira_email" in data: cls.JIRA_EMAIL = _clean(data["jira_email"])
        if "jira_api_token" in data: cls.JIRA_API_TOKEN = _clean(data["jira_api_token"])
        if "jira_project_key" in data: cls.JIRA_PROJECT_KEY = _clean(data["jira_project_key"])
        if "azure_whisper_deployment" in data: cls.AZURE_WHISPER_DEPLOYMENT = _clean(data["azure_whisper_deployment"])

    @classmethod
    def validate(cls):
        # Only Azure AI Foundry core keys are strictly required for startup
        missing_core = []
        core_required = {
            "AZURE_API_KEY": cls.AZURE_API_KEY,
            "AZURE_ENDPOINT": cls.AZURE_ENDPOINT,
        }
        for key, val in core_required.items():
            if not val:
                missing_core.append(key)
        if missing_core:
            raise ValueError(f"[ERROR] Missing core Azure AI env vars in .env file: {missing_core}")
        
        # Check optional integrations and log status
        optionals = {
            "GITHUB_PAT": cls.GITHUB_PAT,
            "NOTION_TOKEN": cls.NOTION_TOKEN,
            "NOTION_DATABASE_ID": cls.NOTION_DATABASE_ID,
            "SENDGRID_API_KEY": cls.SENDGRID_API_KEY,
            "JIRA_API_TOKEN": cls.JIRA_API_TOKEN,
        }
        enabled = []
        disabled = []
        for name, val in optionals.items():
            if val:
                enabled.append(name)
            else:
                disabled.append(name)
        
        print(f"[OK] Core Config validated. Enabled integrations: {enabled}")
        if disabled:
            print(f"[WARNING] Disabled integrations due to missing credentials: {disabled}")

