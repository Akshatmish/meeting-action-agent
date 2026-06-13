# Setup Guide — MeetingActionAgent

## Step 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

## Step 2 — Create .env file

```bash
cp .env.example .env
```

Now fill in your keys:

### Azure API Key
1. Go to: ai.azure.com → your project home page
2. Copy the API key (dots wala box)
3. Paste in AZURE_API_KEY

### GitHub PAT
1. Go to: github.com → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token → select "repo" scope
4. Paste in GITHUB_PAT

### Notion Token
1. Go to: notion.so/my-integrations
2. New Integration → Name: MeetingActionAgent
3. Copy Internal Integration Token
4. Paste in NOTION_TOKEN

### Notion Database ID
1. Create a new page in Notion
2. Add a database (full page)
3. Add columns: Task, Owner, Deadline, Priority, Status, Category, Meeting Date
4. Connect integration: ••• → Connections → MeetingActionAgent
5. Copy ID from URL (the part after notion.so/workspace/)
6. Paste in NOTION_DATABASE_ID

### SendGrid Key
1. Go to: sendgrid.com → Sign up free
2. Settings → API Keys → Create API Key
3. Full access → Create
4. Paste in SENDGRID_API_KEY

## Step 3 — Run the agent

```bash
python main.py
```

## Expected output

```
╔══════════════════════════════════════════════════════╗
║         MeetingActionAgent 🤖                        ║
╚══════════════════════════════════════════════════════╝

✅ Config validated — all keys present
STEP 1: Analyzing transcript with Azure AI + Work IQ
  → Extracted 5 action items
  → Extracted 2 decisions

STEP 2: Creating GitHub Issues...
  ✅ Issue #1 created
  ✅ Issue #2 created
  ...

STEP 3: Creating Notion tasks...
  ✅ Notion task created: Fix login bug
  ✅ Notion summary page created

STEP 4: Sending emails...
  ✅ Email sent to akshat@company.com

✅ MeetingActionAgent pipeline complete!
   GitHub issues created : 5
   Notion pages created  : 6
   Emails sent           : 3
```

## Verify results

- GitHub: github.com/Akshatmish/meeting-action-agent/issues
- Notion: your database page
- Email: check your inbox
