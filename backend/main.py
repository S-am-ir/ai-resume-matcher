from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncpg
import base64
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
from googleapiclient.discovery import build

from database import init_db
from config import settings
from agent.graph import build_graph

# Allow HTTP traffic for local dev
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create temp directory for resume uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background tracking task
    asyncio.create_task(background_tracking_loop())
    yield
    # Shutdown: cleanup if needed

async def background_tracking_loop():
    """Automatically track all users' applications every 60 minutes."""
    print("[BACKGROUND] Starting auto-tracking loop (every 60 minutes)...")
    
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 60 minutes
            
            # Get all users with Gmail credentials
            db_url = settings.SUPABASE_DB_URL
            if not db_url:
                continue
            
            conn = await asyncpg.connect(db_url)
            users = await conn.fetch('SELECT email, imap_password FROM users WHERE imap_password IS NOT NULL')
            
            for user in users:
                email = user['email']
                app_password = user['imap_password']
                
                print(f"[BACKGROUND] Tracking applications for {email}...")
                
                # Invoke tracking agent
                graph = build_graph()
                result = await graph.ainvoke({
                    "messages": [{"role": "user", "content": "Track my applications"}],
                    "user_email": email,
                    "user_resume_data": {"imap_password": app_password}
                })
                
                if result.get("tracking_updates"):
                    print(f"[BACKGROUND] Found {len(result['tracking_updates'])} updates for {email}")
            
            await conn.close()
            print("[BACKGROUND] Tracking cycle complete")
            
        except Exception as e:
            print(f"[BACKGROUND] Error in tracking loop: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying

app = FastAPI(title="Anti-Berojgar API", lifespan=lifespan)

# CORS Configuration - Allow all origins for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Vercel, Railway, localhost)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return {"message": "Welcome to Anti-Berojgar Agent API"}

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), email: Optional[str] = None):
    """Upload resume file and store it for later use. PDF only."""
    try:
        print(f"\n[UPLOAD] === Resume Upload ===")
        print(f"[UPLOAD] email: {email}")
        print(f"[UPLOAD] filename: {file.filename}")
        print(f"[UPLOAD] SUPABASE_DB_URL: {settings.SUPABASE_DB_URL[:50] if settings.SUPABASE_DB_URL else 'None'}...")
        
        # Validate PDF only
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext != 'pdf' and file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted. Please upload a PDF resume."
            )

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        print(f"[UPLOAD] Saving to: {file_path}")

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        print(f"[UPLOAD] File saved successfully")

        # If email provided, save to database
        if email and settings.SUPABASE_DB_URL:
            print(f"[UPLOAD] Attempting to save to DB for email: {email}")
            try:
                conn = await asyncpg.connect(settings.SUPABASE_DB_URL)
                await conn.execute('''
                    INSERT INTO users (email, resume_data)
                    VALUES ($1, $2)
                    ON CONFLICT (email) DO UPDATE SET resume_data = $2
                ''', email, json.dumps({"visual_path": file_path, "original_name": file.filename}))
                await conn.close()
                print(f"[UPLOAD] DB save successful")
            except Exception as db_err:
                print(f"[UPLOAD] DB save failed: {db_err}")
        elif settings.SUPABASE_DB_URL:
            # Save to DB with anonymous email if no email provided
            try:
                anonymous_email = f"anonymous_{uuid.uuid4()}@temp.local"
                conn = await asyncpg.connect(settings.SUPABASE_DB_URL)
                await conn.execute('''
                    INSERT INTO users (email, resume_data)
                    VALUES ($1, $2)
                ''', anonymous_email, json.dumps({"visual_path": file_path, "original_name": file.filename, "anonymous": True}))
                await conn.close()
                # Return the anonymous email for localStorage
                return {
                    "status": "success",
                    "file_path": file_path,
                    "original_name": file.filename,
                    "anonymous_email": anonymous_email,
                    "message": "Resume uploaded successfully (anonymous)"
                }
            except Exception as db_err:
                print(f"Warning: Could not save anonymous resume to DB: {db_err}")

        return {
            "status": "success",
            "file_path": file_path,
            "original_name": file.filename,
            "message": "Resume uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OAuth endpoints removed to support Zero-Cost IMAP setup.
# User identification now happens locally via the "Connect Email" button.

# -----------------------------------------------------------------------------
# Agent Endpoints
# -----------------------------------------------------------------------------
class AgentRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_email: Optional[str] = None
    job_description: Optional[str] = None
    user_resume_data: Optional[Dict[str, Any]] = None

@app.post("/api/agent/invoke")
async def invoke_agent(req: AgentRequest):
    """Invokes the LangGraph agent workflow."""
    try:
        print(f"\n[API] === Agent Invoke Request ===")
        print(f"[API] user_email: {req.user_email}")
        print(f"[API] user_resume_data: {req.user_resume_data}")
        print(f"[API] job_description length: {len(req.job_description) if req.job_description else 0}")
        
        # Start with resume data from request (frontend sends backendPath)
        user_context = req.user_resume_data or {}
        print(f"[API] Initial user_context from request: {user_context}")

        # Try to load additional data from database if email is provided
        if req.user_email and settings.SUPABASE_DB_URL:
            print(f"[API] Attempting DB lookup...")
            try:
                conn = await asyncpg.connect(settings.SUPABASE_DB_URL)
                user_record = await conn.fetchrow(
                    "SELECT id, resume_data FROM users WHERE email = $1",
                    req.user_email
                )
                print(f"[API] DB user_record: {user_record}")
                if not user_record:
                    # Auto-create user if they don't exist (since we skipped OAuth)
                    await conn.execute("INSERT INTO users (email) VALUES ($1)", req.user_email)
                    user_record = await conn.fetchrow("SELECT id, resume_data FROM users WHERE email = $1", req.user_email)
                    print(f"[API] Created new user: {user_record}")

                if user_record:
                    db_resume = user_record.get('resume_data') or {}
                    db_imap = user_record.get('imap_password')

                    resume_dict = db_resume if isinstance(db_resume, dict) else json.loads(db_resume) if db_resume else {}
                    print(f"[API] resume_dict from DB: {resume_dict}")

                    # Merge: request data takes priority, DB data as fallback
                    user_context = {
                        **resume_dict,  # DB data (has visual_path if saved)
                        **user_context,  # Request data (has backendPath from frontend)
                        "imap_password": db_imap
                    }
                await conn.close()
                print(f"[API] DB lookup successful")
            except Exception as db_err:
                print(f"[API] DB lookup failed (continuing with request data): {db_err}")
        else:
            print(f"[API] No DB URL or email, using request data only")

        # Convert backendPath to visual_path if needed
        if user_context and 'backendPath' in user_context and 'visual_path' not in user_context:
            user_context['visual_path'] = user_context['backendPath']
            print(f"[API] Converted backendPath to visual_path: {user_context['visual_path']}")

        print(f"[API] Final user_context: {user_context}")

        graph = build_graph()

        # Convert request messages to LangChain HumanMessage objects
        from langchain_core.messages import HumanMessage
        langchain_messages = []
        for m in req.messages:
            if m.get("content"):
                langchain_messages.append(HumanMessage(content=m["content"]))
        
        # If no messages, add a default one
        if not langchain_messages:
            langchain_messages.append(HumanMessage(content="Tailor my resume"))

        initial_state = {
            "messages": langchain_messages,
            "user_email": req.user_email,
            "user_resume_data": user_context,
            "job_description": req.job_description
        }
        
        # Execute workflow
        result = await graph.ainvoke(initial_state)

        # Extract messages to return
        returned_messages = []
        if "messages" in result:
            for m in result["messages"]:
                if hasattr(m, 'content'):
                    returned_messages.append({"role": "assistant", "content": m.content})
                elif isinstance(m, str):
                    returned_messages.append({"role": "assistant", "content": m})

        # Extract jobs from result
        extracted_jobs = result.get("extracted_jobs", [])

        response_data = {
            "status": "success",
            "messages": returned_messages,
            "mode": result.get("current_mode"),
            "tailored_resume_path": result.get("tailored_resume_path"),
            "match_analysis": result.get("match_analysis"),
            "extracted_jobs": extracted_jobs
        }
        
        print(f"[API] Returning: {response_data}")
        return response_data
    except Exception as e:
        print(f"[API] Error: {e}")
        return {"status": "error", "message": str(e)}

class JobLeadRequest(BaseModel):
    user_email: str
    company: str
    job_title: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    salary_info: Optional[str] = None
    job_description: Optional[str] = None

class EmailSettingsRequest(BaseModel):
    user_email: str
    imap_password: str

class AddJobByUrlRequest(BaseModel):
    user_email: str
    job_url: str

@app.post("/api/jobs/add-by-url")
async def add_job_by_url(req: AddJobByUrlRequest):
    """
    Add a job to track by providing its URL.
    Scrapes the job details automatically and saves to database.
    """
    from job_url_scraper import scrape_job_from_url
    
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    # Scrape job details from URL
    print(f"[API] Scraping job from: {req.job_url}")
    job_data = await scrape_job_from_url(req.job_url)
    
    if not job_data:
        raise HTTPException(
            status_code=400,
            detail="Could not extract job information from this URL. The page may be blocked, require login, or not be a valid job posting."
        )
    
    print(f"[API] Scraped: {job_data.get('job_title')} at {job_data.get('company')}")
    
    try:
        conn = await asyncpg.connect(db_url)
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", req.user_email)
        if not user:
            await conn.close()
            raise HTTPException(status_code=404, detail="User not found. Please log in first.")
        
        await conn.execute('''
            INSERT INTO job_leads (user_id, company, job_title, location, job_url, salary_info, job_description)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', user['id'], 
            job_data.get('company', 'Unknown'),
            job_data.get('job_title', ''),
            job_data.get('location', 'Remote'),
            job_data.get('job_url', ''),
            None,  # salary_info
            job_data.get('job_description', '')
        )
        
        await conn.close()
        
        return {
            "status": "success",
            "message": "Job added to tracking.",
            "job": {
                "company": job_data.get('company'),
                "job_title": job_data.get('job_title'),
                "location": job_data.get('location'),
                "job_url": job_data.get('job_url'),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/save")
async def save_job_lead(req: JobLeadRequest):
    """Saves a job to the applications table for tracking."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database URL not configured")

    try:
        conn = await asyncpg.connect(db_url)
        
        # Get or create user
        user = await conn.fetchrow("SELECT id, imap_password FROM users WHERE email = $1", req.user_email)
        if not user:
            # Auto-create user if they don't exist (since we skipped OAuth)
            await conn.execute("INSERT INTO users (email) VALUES ($1)", req.user_email)
            user = await conn.fetchrow("SELECT id, imap_password FROM users WHERE email = $1", req.user_email)

        # Determine initial status based on Gmail configuration
        initial_status = "Tracking" if user and user.get("imap_password") else "Pending"

        await conn.execute('''
            INSERT INTO job_applications (user_id, company, job_title, job_url, job_description, status, applied_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        ''', user['id'], req.company or 'Unknown', req.job_title, req.job_url, req.job_description, initial_status)

        await conn.close()
        return {"status": "success", "message": "Job added to tracking."}
    except Exception as e:
        print(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/leads")
async def get_job_leads(email: str):
    """Fetch saved job leads for a user."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        return []
        
    try:
        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch('''
            SELECT jl.* FROM job_leads jl
            JOIN users u ON jl.user_id = u.id
            WHERE u.email = $1
            ORDER BY jl.discovered_at DESC
        ''', email)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return []

@app.post("/api/applications/sync")
async def sync_applications(email: str):
    """Triggers the agent to sync application statuses from Gmail."""
    req = AgentRequest(
        messages=[{"role": "user", "content": "Sync my application statuses from Gmail and check for any responses."}],
        user_email=email
    )
    return await invoke_agent(req)

@app.get("/api/resume/download/{filename:path}")
async def download_tailored_resume(filename: str):
    """Serve tailored resume files for download (PDF or HTML)."""
    from fastapi.responses import FileResponse, HTMLResponse

    # Handle HTML paths (prefixed with "html:")
    if filename.startswith("html:"):
        # It's an HTML file fallback
        html_filename = filename[5:]  # Remove "html:" prefix
        file_path = os.path.join("output", html_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="HTML file not found. PDF generation may have failed.")
        
        # Read HTML content and return as HTML response
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content, headers={
            "Content-Disposition": f'attachment; filename="{html_filename}"'
        })
    
    # Default: PDF file
    file_path = os.path.join("output", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )

@app.get("/api/applications")
async def get_applications(email: str):
    """Fetch applications from DB."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        return []

    try:
        conn = await asyncpg.connect(db_url)
        rows = await conn.fetch('''
            SELECT ja.* FROM job_applications ja
            JOIN users u ON ja.user_id = u.id
            WHERE u.email = $1
            ORDER BY ja.applied_at DESC
        ''', email)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"DB Error: {e}")
        return []

@app.delete("/api/applications/{app_id}")
async def delete_application(app_id: str, email: str):
    """Delete a job application."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Verify ownership
        owner = await conn.fetchrow('''
            SELECT ja.id FROM job_applications ja
            JOIN users u ON ja.user_id = u.id
            WHERE ja.id = $1 AND u.email = $2
        ''', app_id, email)
        
        if not owner:
            await conn.close()
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Delete the application
        await conn.execute('DELETE FROM job_applications WHERE id = $1', app_id)
        await conn.close()
        
        return {"status": "success", "message": "Application deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/email")
async def save_email_settings(req: EmailSettingsRequest):
    """Saves user email tracking credentials (IMAP App Password) to the DB."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        conn = await asyncpg.connect(db_url)
        # Check if user exists, if not create them
        await conn.execute('''
            INSERT INTO users (email, imap_password)
            VALUES ($1, $2)
            ON CONFLICT (email) DO UPDATE SET imap_password = $2
        ''', req.user_email, req.imap_password)
        
        # Update all Pending jobs to Tracking now that Gmail is connected
        await conn.execute('''
            UPDATE job_applications ja
            SET status = 'Tracking'
            FROM users u
            WHERE ja.user_id = u.id 
            AND u.email = $1 
            AND ja.status = 'Pending'
        ''', req.user_email)
        
        await conn.close()
        return {"status": "success", "message": "Email settings saved. Auto-tracking started!"}
    except Exception as e:
        print(f"Error saving settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{email}")
async def delete_user_account(email: str):
    """Completely delete user account and all associated data."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Delete all job applications first (foreign key constraint)
        await conn.execute('''
            DELETE FROM job_applications 
            WHERE user_id IN (SELECT id FROM users WHERE email = $1)
        ''', email)
        
        # Delete the user
        await conn.execute('DELETE FROM users WHERE email = $1', email)
        
        await conn.close()
        return {"status": "success", "message": "Account deleted successfully."}
    except Exception as e:
        print(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/reset-tracking")
async def reset_tracking(req: EmailSettingsRequest):
    """Reset Gmail configuration and set all jobs back to Pending."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Clear Gmail password
        await conn.execute('''
            UPDATE users SET imap_password = NULL WHERE email = $1
        ''', req.user_email)
        
        # Reset all jobs to Pending
        await conn.execute('''
            UPDATE job_applications ja
            SET status = 'Pending', gmail_message_id = NULL
            FROM users u
            WHERE ja.user_id = u.id AND u.email = $1
        ''', req.user_email)
        
        await conn.close()
        return {"status": "success", "message": "Tracking reset. Re-connect Gmail to enable auto-tracking."}
    except Exception as e:
        print(f"Error resetting tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings/email")
async def get_email_settings(email: str):
    """Fetch existing email settings (checks if password exists)."""
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        return {"email": email, "has_password": False}
    try:
        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow("SELECT imap_password FROM users WHERE email = $1", email)
        await conn.close()

        has_password = bool(row and row['imap_password'])
        return {
            "email": email,
            "has_password": has_password
        }
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return {"email": email, "has_password": False}

