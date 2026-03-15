"""
Simplified agent nodes - only resume tailoring and application tracking.
No job search functionality.
"""
import os
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .prompts import ROUTER_PROMPT, TAILOR_PROMPT, TRACK_PROMPT
from .llm import get_main_llm


async def route_query(state: AgentState):
    """Router to determine if user wants to tailor resume or track applications."""
    messages = state.get('messages', [])
    if not messages:
        print("[ROUTER] No messages, defaulting to 'tailor'")
        return {"current_mode": "tailor"}

    llm = get_main_llm()
    
    # Get last message content (handle both string and message object)
    last_msg = messages[-1]
    last_msg_content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
    
    print(f"[ROUTER] User message: {last_msg_content[:100]}...")
    
    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_PROMPT),
        last_msg
    ])

    mode = response.content.strip().lower()
    print(f"[ROUTER] LLM response: '{mode}'")
    
    if mode not in ["tailor", "track"]:
        print(f"[ROUTER] Unknown mode '{mode}', defaulting to 'tailor'")
        mode = "tailor"
    else:
        print(f"[ROUTER] Routing to: {mode}")

    return {"current_mode": mode}


async def tailor_resume(state: AgentState):
    """Tailor resume based on job description using Gemini 2.5 Flash."""
    from .tailor import tailor_resume_html

    resume_data = state.get("user_resume_data", {})
    resume_path = resume_data.get("visual_path")
    job_desc = state.get("job_description")

    print(f"\n[TAILOR] Resume Path: {resume_path}")
    print(f"[TAILOR] Job Desc Length: {len(job_desc) if job_desc else 0}")

    if not resume_path:
        print("[ERROR] No resume path provided")
        return {
            "messages": [SystemMessage(content="Error: No resume uploaded. Please upload your resume first.")],
            "errors": ["Missing resume"]
        }

    if not job_desc:
        print("[ERROR] No job description provided")
        return {
            "messages": [SystemMessage(content="Error: No job description provided.")],
            "errors": ["Missing job description"]
        }

    if not os.path.exists(resume_path):
        print(f"[ERROR] Resume file not found at: {resume_path}")
        return {
            "messages": [SystemMessage(content="Error: Resume file not found. Please re-upload your resume.")],
            "errors": ["File not found"]
        }

    result = await tailor_resume_html(resume_path, job_desc)

    print(f"[TAILOR] Result: {result}\n")

    if not result:
        print("[TAILOR] Result is None - returning error")
        return {
            "messages": [SystemMessage(content="Resume tailoring failed.")],
            "errors": ["Failed to generate resume"],
            "match_analysis": None,
            "tailored_resume_path": None
        }

    # Handle mismatch error
    if result.get("error") == "mismatch":
        analysis = result.get("match_analysis", {})
        print(f"[TAILOR] Mismatch: {analysis}")
        return {
            "messages": [SystemMessage(content="Job Mismatch Detected")],
            "match_analysis": analysis,
            "tailored_resume_path": None
        }

    if result.get("pdf_path"):
        filename = os.path.basename(result["pdf_path"])
        download_url = f"/api/resume/download/{filename}"
        return {
            "messages": [SystemMessage(content="Resume tailored successfully!")],
            "match_analysis": result.get("match_analysis"),
            "tailored_resume_path": download_url
        }
    else:
        return {
            "messages": [SystemMessage(content="Resume tailoring failed.")],
            "errors": ["PDF generation failed"],
            "match_analysis": None,
            "tailored_resume_path": None
        }


async def track_applications(state: AgentState):
    """Track job applications via Gmail IMAP - analyzes emails and updates statuses automatically."""
    from .email_tracker import fetch_recent_application_threads
    import asyncpg
    import json
    from datetime import datetime, timedelta
    from config import settings

    user_email = state.get("user_email") or settings.GMAIL_USER
    app_password = state.get("user_resume_data", {}).get("imap_password") or settings.GMAIL_APP_PASSWORD

    if not user_email or not app_password:
        error_msg = SystemMessage(content="Missing Gmail credentials. Please configure your email in settings.")
        return {"messages": [error_msg], "errors": ["Missing Credentials"]}

    # Fetch current applications from DB
    db_url = settings.SUPABASE_DB_URL
    db_apps = []
    if db_url:
        try:
            conn = await asyncpg.connect(db_url)
            rows = await conn.fetch('''
                SELECT ja.id, ja.company, ja.job_title, ja.status, ja.gmail_thread_id, ja.job_url, ja.applied_at, ja.last_checked_at
                FROM job_applications ja
                JOIN users u ON ja.user_id = u.id
                WHERE u.email = $1
            ''', user_email)
            db_apps = [dict(r) for r in rows]
            await conn.close()
        except Exception as e:
            print(f"Error fetching apps for tracking: {e}")

    if not db_apps:
        return {"messages": [SystemMessage(content="No applications to track yet.")]}

    # Step 1: Update time-based statuses (Follow Up / Ghosted)
    print("[TRACK] Checking time-based status updates...")
    now = datetime.now()
    updates_needed = []
    
    for app in db_apps:
        if not app.get('applied_at'):
            continue
            
        applied_date = app['applied_at']
        if hasattr(applied_date, 'date'):
            days_since_applied = (now - applied_date).days
        else:
            days_since_applied = 0
        
        current_status = app.get('status', '').lower()
        
        # Only update if still in Tracking status
        if current_status == 'tracking':
            if days_since_applied >= 7:
                updates_needed.append((app['id'], 'Ghosted', f'No response in {days_since_applied} days'))
                print(f"[TRACK] {app['job_title']} at {app['company']} → Ghosted ({days_since_applied} days)")
            elif days_since_applied >= 5:
                updates_needed.append((app['id'], 'Follow Up', f'Consider following up after {days_since_applied} days'))
                print(f"[TRACK] {app['job_title']} at {app['company']} → Follow Up ({days_since_applied} days)")
    
    # Apply time-based updates
    if updates_needed and db_url:
        conn = await asyncpg.connect(db_url)
        for app_id, new_status, note in updates_needed:
            await conn.execute('''
                UPDATE job_applications 
                SET status = $1, notes = $2, last_checked_at = NOW()
                WHERE id = $3
            ''', new_status, note, app_id)
        await conn.close()
        print(f"[TRACK] Applied {len(updates_needed)} time-based updates")

    # Step 2: Fetch Gmail threads and analyze for responses
    print("[TRACK] Fetching Gmail threads...")
    threads = fetch_recent_application_threads(user_email, app_password)

    if not threads:
        return {
            "messages": [SystemMessage(content=f"Checked Gmail - no new responses found. Tracking {len(db_apps)} applications.")],
            "tracking_updates": []
        }

    # Step 3: Use LLM to match emails to applications and determine status
    llm = get_main_llm()
    
    track_prompt = f"""You are an application tracking assistant. Analyze Gmail threads and match them to job applications.

For each email thread, determine:
1. Which application it matches (by company name or job title)
2. If it's a response FROM the company (not from the user)
3. What type of response: INTERVIEW, OFFER, REJECTION, or FOLLOW_UP_REQUEST
4. Extract the Gmail message ID for linking

Existing Applications:
{json.dumps([{
    "id": app['id'],
    "company": app['company'],
    "job_title": app['job_title'],
    "current_status": app['status']
} for app in db_apps], indent=2)}

Recent Gmail Threads:
{json.dumps(threads, indent=2)}

Output ONLY valid JSON:
{{
  "updates": [
    {{
      "application_id": 123,
      "new_status": "Interview" | "Offered" | "Rejected",
      "gmail_message_id": "thread_id_from_gmail",
      "notes": "Brief summary of response"
    }}
  ],
  "summary": "Found X responses: Y interviews, Z offers, W rejections"
}}

Rules:
- Only update if email is FROM company (not from user)
- Match by company name or job title similarity
- INTERVIEW: Contains words like "interview", "meeting", "call scheduled", "next round"
- OFFER: Contains words like "offer", "welcome aboard", "pleased to offer", "joining"
- REJECTION: Contains words like "not moving forward", "other candidates", "not selected", "thank you for interest"
- Do NOT update if already Interview/Offered/Rejected"""

    response = await llm.ainvoke([
        SystemMessage(content=track_prompt),
        *state.get('messages', [])
    ])

    # Parse LLM response and update database
    try:
        import re
        content = response.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        
        result = json.loads(content)
        
        # Update database with email-based status changes
        if db_url and "updates" in result:
            conn = await asyncpg.connect(db_url)
            for update in result["updates"]:
                app_id = update.get("application_id")
                new_status = update.get("new_status")
                gmail_id = update.get("gmail_message_id")
                notes = update.get("notes", "")
                
                if app_id and new_status:
                    try:
                        await conn.execute('''
                            UPDATE job_applications 
                            SET status = $1, gmail_message_id = $2, notes = $3, last_checked_at = NOW()
                            WHERE id = $4
                        ''', new_status, gmail_id, f"[{new_status}] {notes}", app_id)
                        print(f"[TRACK] Updated application {app_id} → {new_status}")
                    except Exception as e:
                        print(f"[TRACK] Failed to update {app_id}: {e}")
            
            await conn.close()
            
        return {
            "messages": [SystemMessage(content=result.get("summary", "Tracking complete"))],
            "tracking_updates": result.get("updates", [])
        }
        
    except Exception as e:
        print(f"[TRACK] Failed to parse/update: {e}")
        return {"messages": [response]}
