# Anti-Berojgar

> **Job Application Tracker with AI Resume Tailoring & Automatic Email Monitoring**

Tired of applying to jobs and hearing nothing back? This system tracks your applications, auto-tailors your resume for each job, and monitors your Gmail for responses (interviews, offers, rejections) - so you always know where you stand.

Built because I was sick of refreshing my inbox and wondering if companies ghosted me or not.

---

## 🎯 What It Does

### 1. **Resume Tailoring with Job Matching**
Upload your resume + paste a job description. The AI first checks if you're actually a good fit (doesn't waste your time on mismatched roles), then generates a tailored, ATS-optimized resume that highlights your relevant skills.

**Why this matters:** Most resume tailoring tools just rewrite whatever you give them. This one tells you "nah, this job wants 5 years and you got 0 - don't waste your time" OR "you got this, here's a resume that matches what they want."

### 2. **Automatic Application Tracking via Gmail**
Connect your Gmail once. The system checks your inbox every hour for responses from companies. When it finds an interview invite, offer, or rejection - it updates your application status automatically and gives you a direct link to that email.

**Why this matters:** No more manually checking 50 different company portals or refreshing Gmail. You get one dashboard showing exactly where every application stands.

### 3. **Time-Based Status Updates**
No response after 5 days? Marks as "Follow Up". Still nothing after 7 days? Marks as "Ghosted". Knows when to move on.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ANTI-BEROJGAR SYSTEM                             │
│              AI-Powered Job Application Tracker                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │◄───────►│   Backend    │◄───────►│   Database   │
│   React      │   REST  │   FastAPI    │  PostgreSQL         │
│   Vite       │   API   │  LangGraph   │  Supabase           │
│  (Port 5173) │         │  (Port 8000) │                     │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
        ┌──────────────┐               ┌──────────────┐
        │  Agent Graph │               │  JobSpy MCP  │
        │  (LangGraph) │               │  (Job Scraper│
        └──────────────┘               └──────────────┘
                │
                ▼
        ┌──────────────┐
        │  Gmail IMAP  │
        │  (Hourly     │
        │   Auto-Check)│
        └──────────────┘


KEY COMPONENTS:

1. Frontend (React + Vite)
   └─ Resume upload & preview
   └─ Job application dashboard
   └─ Settings (Gmail configuration)
   └─ Tailored resume download

2. Backend (FastAPI + LangGraph)
   └─ Resume parsing (PDF extraction)
   └─ Job matching logic (experience, skills)
   └─ AI resume tailoring (Qwen3-32B, Gemini 2.5)
   └─ Background tracking agent (hourly Gmail checks)

3. Database (PostgreSQL via Supabase)
   └─ Users table (email, resume data, Gmail creds)
   └─ Job applications table (status, tracking info)
   └─ Job leads table (scraped positions)

4. External Services
   └─ Groq API (Qwen3-32B for job matching)
   └─ Gemini 2.5 Flash (resume tailoring)
   └─ Gmail IMAP (email monitoring)
   └─ JobSpy MCP (job scraping from LinkedIn/Indeed)
```

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.10+ (for local dev)
- Groq API key (free): https://console.groq.com/keys
- Gemini API key (free): https://makersuite.google.com/app/apikey

### 1. Clone & Setup
```bash
git clone https://github.com/S-am-ir/Anti-Berojgar.git
cd Anti-Berojgar

# Copy environment template
cp .env.docker.sample .env.docker
# Edit .env.docker with your API keys
```

### 2. Run with Docker
```bash
docker-compose up -d
```

That's it. Open http://localhost:5173 and start tracking.

### 3. First-Time Setup
1. **Upload your resume** (PDF only - ATS friendly)
2. **Connect your Gmail** (Settings → Gmail App Password)
3. **Add jobs** you've applied to
4. **Wait** - the system checks your Gmail every hour

---

## 📋 Features

### Resume Tailoring
- ✅ PDF-only upload (no images - ATS compatibility)
- ✅ Job matching before tailoring (saves time on bad fits)
- ✅ ATS-optimized output (single column, standard fonts)
- ✅ One-page format for entry-level (no fake experience added)
- ✅ Highlights relevant skills from job description

### Application Tracking
- ✅ Manual job addition (title, company, URL, description)
- ✅ Automatic Gmail monitoring (hourly)
- ✅ Status auto-updates: Interview / Offered / Rejected
- ✅ Time-based updates: Follow Up (5d) / Ghosted (7d)
- ✅ Direct email links (click to open Gmail response)
- ✅ Delete applications

### Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python, LangGraph |
| Database | PostgreSQL (Supabase) |
| AI/LLM | Qwen3-32B (Groq), Gemini 2.5 Flash |
| Email | Gmail IMAP |
| Deployment | Docker Compose |

---

## 🧪 Testing

```bash
# Run unit tests
cd backend
python tests/run_tests.py

# Or directly
pytest tests/test_unit.py -v
```

**12 tests covering:**
- Resume PDF validation
- Job matching logic (experience gaps, skills)
- Email subject parsing (interview/offer/rejection detection)
- Gmail link generation
- Time-based status transitions
- API endpoint validation

Tests run automatically on push/PR via GitHub Actions.

---

## 💰 Cost Breakdown

This thing runs on free tiers. Seriously.

| Service | Free Tier | What It Covers |
|---------|-----------|----------------|
| Groq API | ~30 requests/min | Job matching, routing |
| Gemini API | 15 requests/min | Resume tailoring |
| Supabase | 500MB database | ~10,000 applications |
| Gmail IMAP | Free | Unlimited email tracking |

**Real-world usage:** I tracked 50+ applications for 2 months. Total API cost: $0.

If you go heavy (500+ applications, constant tailoring), you might hit rate limits. At that point you're probably employed anyway.

---

## 📁 Project Structure

```
Anti-Berojgar/
├── backend/
│   ├── agent/              # LangGraph agent (tailoring, tracking)
│   ├── main.py             # FastAPI server
│   ├── tests/              # Unit tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Dashboard, Applications, Settings
│   │   └── pages/          # Home page
│   └── package.json
├── .github/workflows/      # CI/CD (auto-run tests)
├── docker-compose.yml      # Docker setup
└── README.md
```

---

## 🤔 Why I Built This

Job hunting sucks. You apply to 100 jobs, hear back from 5, and have no idea what happened to the other 95. Companies ghost you, application portals are garbage, and you're left refreshing Gmail like it's a slot machine.

This system automates the tracking part so you can focus on actually preparing for interviews (or applying to more jobs, whichever).

The resume tailoring came later - realized I was sending the same generic resume everywhere and getting nowhere. Tailoring for each job helped, but doing it manually was exhausting. AI handles it now.

---

## 📝 Demo

See it in action: [demo.md](./demo.md)

---

## 🛠️ Troubleshooting

### Resume tailoring fails
- Check Groq/Gemini API keys in `.env.docker`
- Make sure resume is PDF (not image)
- Job description too short? Paste the full thing

### Gmail tracking not working
- Use **App Password**, not your regular Gmail password
- Enable IMAP in Gmail settings first
- Wait up to 60 minutes for first check (runs hourly)

### Database errors
- Run `docker-compose down -v` to reset (warning: deletes data)
- Check if port 5432 is available

---

## 📄 License

MIT. Use it, break it, fix it, whatever. Just don't blame me if it gets you rejected from Google.

---

## 🙏 Shoutouts

- **Groq** - Free, fast LLM inference (Qwen3-32B is underrated)
- **LangGraph** - Makes agent workflows actually manageable
- **Supabase** - PostgreSQL without the headache

Built with ☕ and frustration during a job search.
