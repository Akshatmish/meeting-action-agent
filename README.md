# MeetingActionAgent 🤖

> **Agents League Hackathon 2026 — Enterprise Agents Track**
> Powered by Azure AI Foundry + Work IQ + GitHub + Notion + SendGrid

## What it does

MeetingActionAgent automatically transforms meeting transcripts into structured actions:

- 📋 **Extracts** action items, owners, deadlines, and decisions using AI
- 🔗 **Creates GitHub Issues** for every technical task automatically
- 📓 **Creates Notion pages** for task tracking and meeting summaries
- 📧 **Sends email summaries** to all participants via SendGrid
- 🧠 **Uses Work IQ** (Microsoft IQ layer) for workplace context enrichment

## Architecture

```
Meeting Transcript
       ↓
Azure AI Foundry (gpt-4.1-mini) + Work IQ
       ↓
  Structured JSON
       ↓
┌──────┬──────┬──────┐
↓      ↓      ↓      ↓
GitHub Notion Email Console
Issues Tasks  Summary  ✅
```

## Microsoft IQ Integration

This project uses **Work IQ** — Microsoft's intelligence layer that:
- Understands workplace context (people, teams, relationships)
- Enriches action items with owner emails and roles
- Enables smarter task assignment based on organizational structure

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Core | Azure AI Foundry + gpt-4.1-mini |
| IQ Layer | Microsoft Work IQ |
| Task tracking | GitHub Issues API |
| Project management | Notion API |
| Email | SendGrid |
| Language | Python 3.10+ |

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/Akshatmish/meeting-action-agent
cd meeting-action-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run
```bash
python main.py
```

## Environment Variables

See `.env.example` for all required variables:
- `AZURE_API_KEY` — Azure AI Foundry API key
- `AZURE_ENDPOINT` — Your Azure endpoint URL
- `GITHUB_PAT` — GitHub Personal Access Token (repo scope)
- `NOTION_TOKEN` — Notion integration token
- `NOTION_DATABASE_ID` — Notion database ID
- `SENDGRID_API_KEY` — SendGrid API key

## Demo

[Demo video link here]

## License

MIT
