"""
FastAPI Server for MeetingActionAgent
Provides Web API endpoints for meeting recording, transcription, and task assignment.
"""
import os
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from main import run as run_pipeline
from agent import transcribe_audio, reset_azure_client
from logger import get_logger

logger = get_logger("web_server")

app = FastAPI(
    title="MeetingActionAgent",
    description="Azure AI Foundry + Work IQ powered meeting orchestrator",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static folder exists
os.makedirs("static", exist_ok=True)


@app.post("/api/config")
def update_config(config: dict):
    try:
        Config.override(config)
        reset_azure_client()
        logger.info("API Configuration dynamically overridden by client request.")
        return {"status": "success", "message": "Configuration successfully updated."}
    except Exception as e:
        logger.error(f"Failed to override config: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/config")
def get_config():
    # Helper to mask secrets
    def mask(val: str) -> str:
        if not val:
            return ""
        if len(val) <= 8:
            return "********"
        return val[:4] + "********" + val[-4:]

    return {
        "azure_api_key": mask(Config.AZURE_API_KEY),
        "azure_endpoint": Config.AZURE_ENDPOINT,
        "azure_model": Config.AZURE_MODEL,
        "azure_api_version": Config.AZURE_API_VERSION,
        "github_pat": mask(Config.GITHUB_PAT),
        "github_repo": Config.GITHUB_REPO,
        "notion_token": mask(Config.NOTION_TOKEN),
        "notion_database_id": mask(Config.NOTION_DATABASE_ID),
        "sendgrid_api_key": mask(Config.SENDGRID_API_KEY),
        "from_email": Config.FROM_EMAIL,
        "work_iq_endpoint": Config.WORK_IQ_ENDPOINT,
        "work_iq_api_key": mask(Config.WORK_IQ_API_KEY),
        "jira_url": Config.JIRA_URL,
        "jira_email": Config.JIRA_EMAIL,
        "jira_api_token": mask(Config.JIRA_API_TOKEN),
        "jira_project_key": Config.JIRA_PROJECT_KEY,
        "azure_whisper_deployment": Config.AZURE_WHISPER_DEPLOYMENT,
    }


@app.get("/api/status")
def get_status():
    """
    Check configuration status of core and optional integrations
    """
    return {
        "azure": bool(Config.AZURE_API_KEY and Config.AZURE_ENDPOINT),
        "github": bool(Config.GITHUB_PAT),
        "notion": bool(Config.NOTION_TOKEN and Config.NOTION_DATABASE_ID),
        "sendgrid": bool(Config.SENDGRID_API_KEY),
        "jira": bool(Config.JIRA_API_TOKEN and Config.JIRA_URL),
        "work_iq": bool(Config.WORK_IQ_ENDPOINT and Config.WORK_IQ_API_KEY),
    }


@app.post("/api/process")
async def process_meeting(
    transcript: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    attendee_emails: Optional[str] = Form(None),
    organizer_name: Optional[str] = Form(None),
    organizer_email: Optional[str] = Form(None),
    meeting_url: Optional[str] = Form(None)
):
    """
    Accepts text transcript or audio file, transcribes via Whisper (if audio), 
    and runs the main pipeline.
    """
    try:
        # Check core requirements
        if not Config.AZURE_API_KEY or not Config.AZURE_ENDPOINT:
            raise HTTPException(
                status_code=400, 
                detail="Azure OpenAI is not configured. Please fill in AZURE_API_KEY and AZURE_ENDPOINT in your .env file."
            )

        emails_list = []
        if attendee_emails:
            import re
            raw_emails = re.split(r'[,\r\n;]+', attendee_emails)
            emails_list = [e.strip() for e in raw_emails if e.strip()]

        final_transcript = ""

        # Handle audio file upload
        if file:
            logger.info(f"Received audio file upload: {file.filename}")
            temp_dir = "temp_audio"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file.filename)
            
            # Save file temporarily
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            try:
                final_transcript = transcribe_audio(temp_path)
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Whisper transcription failed: {str(e)}"
                )
            finally:
                # Clean up local temporary file
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as clean_err:
                        logger.warning(f"Failed to remove temp file: {clean_err}")
        else:
            final_transcript = transcript

        if not final_transcript or not final_transcript.strip():
            raise HTTPException(
                status_code=400, 
                detail="Please provide a text transcript or record/upload a meeting audio file."
            )

        result = run_pipeline(
            transcript=final_transcript, 
            attendee_emails=emails_list,
            organizer_name=organizer_name,
            organizer_email=organizer_email,
            meeting_url=meeting_url
        )
        return result

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server processing error: {str(e)}"}
        )


# Mount static assets
app.mount("/", StaticFiles(directory="static", html=True), name="static")
