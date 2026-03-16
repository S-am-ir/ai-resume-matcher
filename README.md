# Anti-Berojgar 🎯

**AI-powered job application tracker that tailors your resume and automatically tracks applications via Gmail.**

Anti-Berojgar (Hindi for "Unemployed") is an intelligent job search assistant that:
- ✨ Tailors your resume to each job description using AI
- 🎯 Evaluates job-resume matching before you apply
- 📧 Automatically tracks application responses from Gmail
- ⏰ Updates statuses based on email responses AND time elapsed
- 🔄 Runs hourly automated tracking via GitHub Actions

---

## 🚀 Quick Start

### Option 1: Deploy on Hugging Face Spaces (Recommended - 100% Free)

#### Step 1: Create Supabase Database (5 minutes)

1. Go to https://supabase.com and sign up
2. Click **"New Project"**
3. Fill in:
   - **Project name**: `anti-berojgar-db`
   - **Database password**: Save this securely!
   - **Region**: Choose closest to you
4. Wait 2-3 minutes for provisioning
5. Go to **SQL Editor** and run:

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

-- Job Leads table (for discovered jobs)
CREATE TABLE IF NOT EXISTS job_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    company TEXT NOT NULL,
    job_title TEXT NOT NULL,
    location TEXT,
    job_url TEXT,
    salary_info TEXT,
    job_description TEXT,
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    is_picked BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON job_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON job_leads(user_id);
```

6. Go to **Project Settings** → **Database** → Copy **Connection String** (Pooler mode, port 6543)

#### Step 2: Create Hugging Face Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Owner**: Your username
   - **Space name**: `anti-berojgar`
   - **License**: MIT
   - **SDK**: **Docker** ⚠️ (Critical - don't select Gradio/Streamlit)
4. Click **"Create Space"**

#### Step 3: Connect GitHub

1. In your HF Space, go to **Settings** tab
2. Scroll to **"GitHub repository"**
3. Click **"Connect a GitHub repository"**
4. Enter: `S-am-ir/Anti-Berojgar`
5. Click **"Connect"**

#### Step 4: Add Environment Variables

In HF Space Settings → **"Repository secrets"**, add these:

| Variable | Value | Where to Find |
|----------|-------|---------------|
| `SUPABASE_DB_URL` | `postgresql://postgres.xxx:PASSWORD@host.pooler.supabase.com:6543/postgres` | Supabase → Settings → Database → Connection String |
| `SUPABASE_URL` | `https://YOUR_PROJECT_REF.supabase.co` | Supabase → Settings → API → Project URL |
| `SUPABASE_KEY` | `eyJhbG...` (anon public key) | Supabase → Settings → API → anon public key |
| `GEMINI_API_KEY` | `AIzaSy...` | https://aistudio.google.com/apikey |
| `GROQ_API_KEY` | `gsk_...` | https://console.groq.com/keys |
| `DEEPSEEK_API_KEY` | `sk-...` | https://platform.deepseek.com/ |
| `PORT` | `7860` | (Fixed for HF Spaces) |

#### Step 5: Wait for Deployment

- HF will build the Docker container (~5-7 minutes first time)
- Once status shows **"Running"** (green), your app is live!
- URL: `https://huggingface.co/spaces/YOUR_USERNAME/anti-berojgar`

---

### Option 2: Local Development

#### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (local or Supabase)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
cp .env.example .env  # Edit if needed
npm run dev
```

Backend: http://localhost:8000
Frontend: http://localhost:5173

---

## 🤖 Automated Tracking Setup

### How It Works

The app uses **GitHub Actions** to run automated tracking every hour:

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Hourly)                   │
│  Cron: "0 * * * *" → Runs at minute 0 of every hour         │
│         ↓                                                    │
│  HTTP POST to: /api/applications/sync?email=user@gmail.com  │
│         ↓                                                    │
│  HF Space wakes up → Runs tracking agent                    │
│         ↓                                                    │
│  Agent checks Gmail IMAP → Updates database                 │
│         ↓                                                    │
│  Returns results → GitHub logs the output                   │
└─────────────────────────────────────────────────────────────┘
```

### Workflow File

The GitHub Action is already configured in `.github/workflows/tracking.yml`:

```yaml
name: Auto Track Job Applications

on:
  schedule:
    - cron: '0 * * * *'  # Every hour at minute 0
  workflow_dispatch:      # Manual trigger option
    inputs:
      email:
        description: 'Email to track'
        required: true
        default: 'your-email@gmail.com'

jobs:
  track-applications:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Tracking
        run: |
          curl "https://YOUR-HF-SPACE.hf.space/api/applications/sync?email=your-email@gmail.com"
```

### Enable Automated Tracking

1. **Fork the repository** to your GitHub account
2. Go to **Settings** → **Actions** → **General**
3. Under **"Actions permissions"**, select **"Allow all actions"**
4. Go to **Actions** tab → Select **"Auto Track Job Applications"**
5. Click **"Enable workflow"**

### Manual Trigger (Test It)

1. Go to **Actions** tab in your GitHub repo
2. Click **"Auto Track Job Applications"** workflow
3. Click **"Run workflow"** dropdown
4. Click **"Run workflow"** button
5. Watch the logs in real-time (~30 seconds)

### What Gets Tracked

The agent checks Gmail for:
- **Interview invites** → Status: "Interview"
- **Offer letters** → Status: "Offered"
- **Rejection emails** → Status: "Rejected"
- **Follow-up requests** → Status: "Follow Up"
- **No response after 5 days** → Auto-marks: "Follow Up"
- **No response after 7 days** → Auto-marks: "Ghosted"

---

## 📧 Gmail Configuration (Critical for Tracking)

### Why Gmail Tracking Matters

Without Gmail integration:
- ❌ No automatic status updates
- ❌ No interview/rejection detection
- ❌ Manual tracking required

With Gmail integration:
- ✅ Automatic detection of company responses
- ✅ Real-time status updates
- ✅ Direct links to response emails
- ✅ Time-based follow-up reminders

### Setup Steps

1. **Enable 2FA on Google Account**:
   - Go to https://myaccount.google.com/security
   - Enable **2-Step Verification**

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select app: **Mail**
   - Select device: **Other** → Name: `Anti-Berojgar`
   - Copy the 16-character password

3. **Add to HF Space**:
   - Go to your HF Space Settings → Repository secrets
   - Add: `GMAIL_APP_PASSWORD` = (the 16-char password)
   - Add: `GMAIL_USER` = your-email@gmail.com

4. **In the App**:
   - Go to Settings page
   - Enter your Gmail address
   - Enter the App Password (NOT your regular password)
   - Click "Save"
   - Status changes from "Pending" → "Tracking"

---

## 🔒 Security: IMAP Password Encryption

### Overview

Anti-Berojgar uses **Fernet symmetric encryption** to protect Gmail IMAP passwords stored in the database. This ensures that even if the database is compromised, your Gmail credentials remain secure.

### How It Works

1. **Encryption at Rest**: When you save your Gmail App Password, it's encrypted using Fernet (AES-128-CBC) before being stored in Supabase
2. **Decryption on Use**: When the tracking agent runs, it decrypts the password in memory only for the IMAP connection
3. **Key Security**: The encryption key is stored ONLY in HF Spaces secrets - never in code or database

### Setup for Deployment

**Generate an encryption key ONCE:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

This outputs something like: `ZmDd5jQqK8H3yL9mN2pR7sT1vW4xY6zA8bC0dE2fG5h=`

**Add to HF Spaces secrets:**
1. Go to your HF Space → Settings → Repository secrets
2. Add new secret: `ENCRYPTION_KEY` = (the generated key)
3. Save

⚠️ **CRITICAL**: 
- **NEVER lose this key** - all encrypted passwords become unrecoverable
- **NEVER commit to git** - always store in secrets only
- **Generate once** - use the same key for the lifetime of your deployment

### What If I Lose the Key?

If the encryption key is lost:
1. Existing encrypted passwords cannot be decrypted
2. Users must re-enter their Gmail App Passwords
3. The app will still work - just re-save credentials

### Why Not Hash the Password?

Hashing is one-way (good for login passwords), but IMAP passwords need to be:
- **Reversible**: We need the actual password to log in to Gmail
- **Secure at rest**: Encrypted in the database
- **Fast**: No performance impact on tracking

Fernet provides perfect security for this use case.

### Backward Compatibility

The encryption system is **backward compatible**:
- If encryption is not configured → passwords stored as plaintext (still works)
- If encryption is configured → new passwords encrypted, old ones detected and used
- Graceful fallback if decryption fails → treats as plaintext

---

## 🏗️ Architecture Deep Dive

### System Overview

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

### Component Breakdown

#### Frontend (React + TypeScript + Vite)

**Key Files:**
- `frontend/src/App.tsx` - Main app router and layout
- `frontend/src/pages/Home.tsx` - Resume upload and job matching
- `frontend/src/components/Applications.tsx` - Application dashboard
- `frontend/src/components/ResumeSetup.tsx` - Resume upload form
- `frontend/src/components/Settings.tsx` - Gmail configuration
- `frontend/src/api.ts` - API client with error handling

**Flow:**
1. User uploads PDF resume → Frontend sends to `/api/resume/upload`
2. Backend saves file → Returns `backendPath`
3. User enters job description → Frontend calls `/api/agent/invoke`
4. Backend processes → Returns tailored resume path
5. Frontend creates download link → User downloads PDF

#### Backend (FastAPI + Python)

**Key Files:**
- `backend/main.py` - FastAPI app, all REST endpoints
- `backend/db_helpers.py` - Supabase HTTP client wrappers
- `backend/database.py` - Supabase client initialization
- `backend/config.py` - Environment variable management
- `backend/agent/graph.py` - LangGraph workflow builder
- `backend/agent/nodes.py` - Agent node implementations
- `backend/agent/tailor.py` - Resume tailoring logic
- `backend/agent/email_tracker.py` - Gmail IMAP client
- `backend/agent/llm.py` - LLM configuration (Gemini, Groq)

**Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/resume/upload` | POST | Upload PDF resume |
| `/api/resume/download/{filename}` | GET | Download tailored resume |
| `/api/agent/invoke` | POST | Trigger agent workflow |
| `/api/jobs/save` | POST | Save job application |
| `/api/applications` | GET | Fetch user's applications |
| `/api/applications/{id}` | DELETE | Delete application |
| `/api/applications/sync` | GET | Trigger Gmail tracking |
| `/api/settings/email` | POST/GET | Configure Gmail credentials |
| `/api/users/{email}` | DELETE | Delete user account |

#### Database (Supabase PostgreSQL)

**Tables:**

**`users`**
- `id` (UUID) - Primary key
- `email` (TEXT) - Unique user identifier
- `name` (TEXT) - Display name
- `resume_data` (JSONB) - Stored resume metadata
- `imap_password` (TEXT) - Encrypted Gmail app password
- `created_at` (TIMESTAMPTZ) - Registration timestamp

**`job_applications`**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key → users.id
- `company` (TEXT) - Company name
- `job_title` (TEXT) - Position applied for
- `job_description` (TEXT) - Full job description
- `status` (TEXT) - Pending/Tracking/Interview/Offered/Rejected/Ghosted
- `applied_at` (TIMESTAMPTZ) - Application date
- `tailored_resume_path` (TEXT) - Path to generated resume
- `gmail_message_id` (TEXT) - Link to response email
- `last_checked_at` (TIMESTAMPTZ) - Last tracking check

**`job_leads`**
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key → users.id
- `company`, `job_title`, `location`, `job_url`, `salary_info`
- `discovered_at` (TIMESTAMPTZ) - When job was found

#### AI/LLM Layer

**Models Used:**
1. **Gemini 2.0 Flash** (Google) - Resume tailoring, document analysis
2. **Groq Llama 3.1** (Meta) - Job matching, routing decisions
3. **DeepSeek V3** (DeepSeek) - Backup LLM, structured output

**Why Multiple LLMs?**
- **Cost optimization**: Different models have different free tiers
- **Specialization**: Gemini excels at document understanding, Groq at speed
- **Redundancy**: If one API fails, fallback to another

**LangGraph Workflow:**
```
User Input → Router Node → [Tailor | Track] → Result
                │
                ├─→ Tailor Request → Mismatch Check → Generate Resume
                │
                └─→ Track Request → Gmail IMAP → LLM Analysis → Update DB
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/tracking.yml`

**Triggers:**
1. **Scheduled**: Every hour at minute 0 (`cron: '0 * * * *'`)
2. **Manual**: Via GitHub Actions UI (`workflow_dispatch`)

**What It Does:**
```yaml
1. GitHub scheduler wakes up at :00
   ↓
2. Sends HTTP GET to HF Space endpoint
   ↓
3. HF Space container wakes up (if sleeping)
   ↓
4. FastAPI receives /api/applications/sync
   ↓
5. Calls invoke_agent() with user's email
   ↓
6. Agent's track_applications() node runs
   ↓
7. Connects to Gmail IMAP
   ↓
8. Fetches recent emails (last 10)
   ↓
9. LLM analyzes emails → matches to applications
   ↓
10. Updates database with new statuses
   ↓
11. Returns summary to GitHub Actions
   ↓
12. GitHub logs the results
```

**Example Output:**
```
🔄 Starting job application tracking...
Response: {"status": "success", "messages": ["Found 2 updates: 1 Interview, 1 Follow-up"]}
HTTP Status: 200
✅ Tracking completed successfully!
```

---

## 💰 Cost Breakdown

**100% Free** with these limits:

| Service | Free Tier | Usage |
|---------|-----------|-------|
| **Hugging Face Spaces** | Unlimited | Hosting (CPU, 16GB RAM) |
| **Supabase** | 500MB DB | ~10,000+ applications |
| **Gemini API** | 1500 req/day | ~50 resumes/day |
| **Groq** | Free tier | ~100 matching checks/day |
| **DeepSeek** | 5M tokens/month | Backup LLM |
| **GitHub Actions** | 2000 minutes/month | ~60 hours of tracking |
| **Gmail IMAP** | Free | Unlimited tracking |

**Real-world usage:**
- 100 applications/month → Uses ~10% of Gemini quota
- Hourly tracking → Uses ~50 GitHub Actions minutes/month
- Database storage → ~50MB for 1000 applications

---

## 🧪 Testing

### Manual Testing Checklist

1. **Resume Upload**:
   - [ ] Upload PDF resume
   - [ ] Verify file saved in `backend/uploads/`
   - [ ] Check database entry created

2. **Job Matching**:
   - [ ] Enter job description
   - [ ] Click "Check & Tailor"
   - [ ] Verify LLM returns "tailor" or "track" mode
   - [ ] Check mismatch detection works

3. **Resume Tailoring**:
   - [ ] Wait for AI processing (~30 seconds)
   - [ ] Download link appears
   - [ ] PDF downloads successfully
   - [ ] Resume contains job-specific keywords

4. **Application Tracking**:
   - [ ] Save a job application
   - [ ] Configure Gmail credentials
   - [ ] Status changes to "Tracking"
   - [ ] Trigger manual sync (GitHub Actions)
   - [ ] Verify Gmail emails checked
   - [ ] Status updates if response found

5. **Time-Based Updates**:
   - [ ] Create application with old date
   - [ ] Run tracking
   - [ ] Verify "Ghosted" after 7 days
   - [ ] Verify "Follow Up" after 5 days

### Automated Tests

```bash
cd backend
pytest tests/ -v
```

**Test Coverage:**
- Unit tests for resume parser
- Integration tests for agent workflow
- Mock tests for Gmail IMAP
- Database migration tests

---

## 🐛 Troubleshooting

### "No resume uploaded" Error

**Cause:** File upload failed or database save failed.

**Fix:**
1. Check HF Space logs for upload errors
2. Verify `SUPABASE_DB_URL` is correct
3. Ensure PDF file is valid (not corrupted)

### Database Connection Errors

**Cause:** Supabase URL incorrect or network blocked.

**Fix:**
1. Use **Pooler** connection string (port 6543)
2. Verify password is correct (no typos)
3. Check Supabase project is active

### Gmail Tracking Not Working

**Cause:** Wrong password or 2FA not enabled.

**Fix:**
1. Enable 2FA on Google Account
2. Use **App Password**, not regular password
3. Verify `GMAIL_USER` matches the email
4. Check IMAP is enabled in Gmail settings

### GitHub Actions Not Running

**Cause:** Actions disabled or permissions wrong.

**Fix:**
1. Go to Repo Settings → Actions → Enable
2. Check workflow file syntax
3. Manually trigger to test

### HF Space Shows "Error"

**Cause:** Missing environment variables or build failed.

**Fix:**
1. Check all 7 secrets are added
2. Review build logs for errors
3. Restart the Space (Settings → Factory reboot)

---

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [Gmail IMAP Guide](https://support.google.com/mail/answer/7126229)
- [GitHub Actions Cron Syntax](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule)
- [Hugging Face Spaces Docker](https://huggingface.co/docs/hub/spaces-sdks-docker)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

MIT License - Free for personal and commercial use.

---

## 🙏 Acknowledgments

- Built for job seekers tired of manual tracking
- Inspired by the frustration of ghosting after interviews
- Made possible by free tiers of amazing services

---

**Built with ❤️ by S-amir** | [GitHub](https://github.com/S-am-ir/Anti-Berojgar) | [Live Demo](https://huggingface.co/spaces/S-a-mir/anti-berojgar)
