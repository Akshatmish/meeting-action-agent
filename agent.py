"""
Azure AI Foundry Agent
Analyzes meeting transcripts using gpt-4.1-mini
Integrated with Work IQ for people context
"""
import json
import re
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config
from logger import get_logger
from work_iq import build_work_iq_prompt_context, get_people_context, enrich_action_items

logger = get_logger("agent")

_client = None

def reset_azure_client():
    global _client
    _client = None

def get_azure_client():
    global _client
    if _client is None:
        # Check if the keys are set. We don't want initialization to fail at import time.
        if not Config.AZURE_API_KEY or not Config.AZURE_ENDPOINT:
            raise ValueError("❌ Azure OpenAI configuration (AZURE_API_KEY / AZURE_ENDPOINT) is missing. Please check your .env file.")
        _client = AzureOpenAI(
            api_key=Config.AZURE_API_KEY,
            api_version=Config.AZURE_API_VERSION,
            azure_endpoint=Config.AZURE_ENDPOINT
        )
    return _client


BASE_SYSTEM_PROMPT = """
You are an enterprise AI assistant (MeetingActionAgent) that analyzes 
meeting transcripts and extracts structured information.

Your job:
1. Read the meeting transcript carefully
2. Extract all action items with owners and deadlines
3. Identify key decisions made
4. Generate follow-up email drafts for each participant
5. Use Work IQ context (if provided) to enrich owner information

Always return ONLY valid JSON — no extra text, no markdown backticks.
Return exactly this format:
{
  "summary": "2-3 sentence meeting summary",
  "participants": ["name1", "name2"],
  "action_items": [
    {
      "task": "clear description of the task",
      "owner": "person responsible",
      "deadline": "specific date or timeframe",
      "priority": "high/medium/low",
      "category": "technical/business/admin"
    }
  ],
  "decisions": [
    "decision 1",
    "decision 2"
  ],
  "follow_up_emails": [
    {
      "to": "person name or email",
      "subject": "email subject",
      "body": "professional email body"
    }
  ]
}
"""


def _extract_participants(transcript: str) -> list:
    """Extract participant names from transcript."""
    lines = transcript.strip().split("\n")
    names = set()
    blacklist = {"meeting", "date", "attendees", "subject", "time", "location", "duration", "note"}
    for line in lines:
        line_stripped = line.strip()
        if "Attendees:" in line or "attendees:" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                for name in parts[1].split(","):
                    name_clean = name.strip()
                    if name_clean and name_clean.lower() not in blacklist:
                        names.add(name_clean)
        else:
            # Also catch "Name: " dialogue patterns, allowing multi-word names (e.g. Akshat Mishra)
            match = re.match(r"^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*):\s", line_stripped)
            if match:
                name_found = match.group(1).strip()
                if name_found.lower() not in blacklist:
                    names.add(name_found)
    return list(names)



@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def analyze_transcript(transcript: str) -> dict:
    """
    Main function — send transcript to Azure AI agent.
    Integrates Work IQ context into the prompt.
    """
    logger.info("Analyzing meeting transcript with Azure AI Foundry...")

    # Extract participants for Work IQ
    participants = _extract_participants(transcript)
    logger.info(f"Participants found: {participants}")

    # Get Work IQ context
    work_iq_context_str = build_work_iq_prompt_context(participants)
    work_iq_data = get_people_context(participants)

    # Build enriched system prompt with Work IQ
    system_prompt = BASE_SYSTEM_PROMPT
    if work_iq_context_str:
        system_prompt += f"\n\n{work_iq_context_str}"
        logger.info("Work IQ context injected into prompt")

    # Call Azure AI Foundry
    response = get_azure_client().chat.completions.create(
        model=Config.AZURE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this meeting transcript:\n\n{transcript}"}
        ],
        temperature=0.1,
        max_tokens=2000
    )

    raw = response.choices[0].message.content.strip()

    # Clean if wrapped in backticks
    if raw.startswith("```"):
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()

    result = json.loads(raw)

    # Enrich action items with Work IQ people context
    if result.get("action_items"):
        result["action_items"] = enrich_action_items(
            result["action_items"],
            work_iq_data
        )

    logger.info(f"Extracted {len(result.get('action_items', []))} action items")
    logger.info(f"Extracted {len(result.get('decisions', []))} decisions")
    return result


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe a meeting audio file using Azure OpenAI Whisper deployment.
    """
    logger.info(f"Transcribing audio file with Whisper: {audio_file_path}")
    
    deployment = Config.AZURE_WHISPER_DEPLOYMENT
    if not deployment:
        logger.warning("AZURE_WHISPER_DEPLOYMENT not set — defaulting to 'whisper'")
        deployment = "whisper"
        
    try:
        with open(audio_file_path, "rb") as f:
            response = get_azure_client().audio.transcriptions.create(
                model=deployment,
                file=f
            )
        transcript = response.text
        logger.info("Whisper transcription successful")
        return transcript
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise e

