# Anti-Berojgar 🎯

AI-powered job application tracker that tailors your resume and automatically tracks applications via Gmail.

## Features

- 📄 **Resume Tailoring** - AI customizes your resume for each job description
- 🎯 **Job Matching** - Evaluates if you're a good fit before tailoring
- 📧 **Gmail Auto-Tracking** - Monitors your inbox for interview invites, offers, rejections
- ⏰ **Smart Status Updates** - Auto-marks as "Follow Up" (5 days) or "Ghosted" (7 days)
- 📊 **Application Dashboard** - Track all your applications in one place

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Resume     │  │   Job        │  │  Application │         │
│  │   Upload     │  │   Matching   │  │  Dashboard   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  Resume Parser │  │  Match Analyzer│  │  Gmail Tracker │    │
│  │  (PDF → Text)  │  │  (LLM Eval)    │  │  (IMAP Poll)   │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Agent Workflow                     │  │
│  │  ┌─────────┐    ┌──────────┐    ┌──────────┐            │  │
│  │  │ Tailor  │───▶│ Mismatch │───▶│ Generate │            │  │
│  │  │ Request │    │  Check   │    │  Resume  │            │  │
│  │  └─────────┘    └──────────┘    └──────────┘            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Gemini  │  │  Groq    │  │ Supabase │
        │  2.0     │  │  Llama   │  │ Postgres │
        │  Flash   │  │  3.1     │  │  (Free)  │
        └──────────┘  └──────────┘  └──────────┘
```

## Quick Start

### 1. Deploy on Hugging Face Spaces (Recommended)

1. **Create Supabase Database** (free):
   - Go to https://supabase.com
   - Create new project
   - Copy the **Connection String** (Pooler mode)

2. **Create HF Space**:
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `anti-berojgar`
   - License: MIT
   - **Select "Docker" as SDK**
   - Click "Create Space"

3. **Connect GitHub**:
   - In your HF Space, go to **Settings**
   - Scroll to "Repository details"
   - Click "Connect GitHub Repo"
   - Select your `Anti-Berojgar` repository

4. **Add Environment Variables** (in HF Space Settings → Variables):
   ```
   SUPABASE_DB_URL=postgresql://...
   GEMINI_API_KEY=AIzaSy...
   GROQ_API_KEY=gsk_...
   DEEPSEEK_API_KEY=sk-...
   ```

5. **Wait for deployment** (~5 minutes)

### 2. Set Up Database

Run this SQL in your Supabase SQL Editor:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    oauth_token JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resume_data JSONB,
    imap_password TEXT
);

-- Job Applications table
CREATE TABLE IF NOT EXISTS job_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_description TEXT,
    status TEXT DEFAULT 'Pending',
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    last_checked_at TIMESTAMPTZ,
    tailored_resume_path TEXT,
    agent_notes TEXT,
    gmail_message_id TEXT,
    gmail_thread_id TEXT,
    job_url TEXT,
    location TEXT,
    salary_info TEXT
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON job_applications(status);
```

### 3. Get API Keys

| Service | Purpose | Get From |
|---------|---------|----------|
| **Gemini** | Resume tailoring (free, 1500 req/day) | https://aistudio.google.com/apikey |
| **Groq** | Fast LLM inference (free tier) | https://console.groq.com/keys |
| **DeepSeek** | Backup LLM (free, 5M tokens/mo) | https://platform.deepseek.com/ |

### 4. Configure Gmail (Optional but Recommended)

1. Enable 2FA on your Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Create app password:
   - App: **Mail**
   - Device: **Other** → Name: `Anti-Berojgar`
4. Copy the 16-character password
5. Add to HF Space variables as `GMAIL_APP_PASSWORD`

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (or use Supabase free tier)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your keys
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env  # Edit if needed
npm run dev
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
Anti-Berojgar/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── agent/
│   │   ├── graph.py         # LangGraph workflow
│   │   ├── nodes.py         # Agent nodes (tailor, track)
│   │   ├── tailor.py        # Resume tailoring logic
│   │   ├── email_tracker.py # Gmail IMAP tracking
│   │   └── llm.py          # LLM configuration
│   ├── config.py            # Environment config
│   └── database.py          # DB initialization
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main app component
│   │   ├── pages/
│   │   │   ├── Home.tsx     # Resume upload & tailoring
│   │   │   └── ...
│   │   └── api.ts           # API client
│   └── package.json
├── Dockerfile               # HF Spaces deployment
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite |
| **Backend** | FastAPI, Python 3.11 |
| **AI/LLM** | LangChain, LangGraph, Gemini 2.0 Flash, Groq |
| **Database** | PostgreSQL (Supabase) |
| **Email** | Gmail IMAP |
| **Deployment** | Hugging Face Spaces Docker |

---

## Cost

**100% Free** when using:
- Hugging Face Spaces (free Docker hosting)
- Supabase (free tier: 500MB DB, enough for 10k+ applications)
- Gemini API (free: 1500 requests/day)
- Groq (free tier available)
- Gmail IMAP (free)

---

## Troubleshooting

### "No resume uploaded" error
- Make sure you uploaded a PDF before clicking "Check & Tailor"
- Check HF Space logs for upload errors

### Database connection errors
- Verify `SUPABASE_DB_URL` is correct (use Pooler URL)
- Make sure you ran the SQL migration

### Gmail tracking not working
- Ensure 2FA is enabled on Google Account
- Use App Password, not regular password
- Check `GMAIL_USER` matches the email

---

## License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ for job seekers everywhere**
