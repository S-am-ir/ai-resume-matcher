"""Database helpers using Supabase HTTP client (works on HF Spaces)."""
from database import supabase
from typing import Optional, Dict, Any, List
import uuid

def get_or_create_user(email: str) -> Optional[Dict[str, Any]]:
    """Get or create user by email."""
    if not supabase:
        return None
    
    try:
        # Try to get existing user
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # Create new user
        new_user = {"email": email}
        response = supabase.table("users").insert(new_user).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error in get_or_create_user: {e}")
        return None

def save_resume(email: str, resume_data: Dict[str, Any]) -> bool:
    """Save resume data for user."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(email)
        if not user:
            return False
        
        response = supabase.table("users").update({"resume_data": resume_data}).eq("email", email).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error saving resume: {e}")
        return False

def save_job_application(user_email: str, company: str, job_title: str, 
                         job_description: Optional[str] = None, 
                         job_url: Optional[str] = None,
                         status: str = "Pending") -> bool:
    """Save a job application."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(user_email)
        if not user:
            return False
        
        application = {
            "user_id": user["id"],
            "company": company or "Unknown",
            "job_title": job_title,
            "job_description": job_description,
            "job_url": job_url,
            "status": status
        }
        
        response = supabase.table("job_applications").insert(application).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error saving job application: {e}")
        return False

def get_applications(email: str) -> List[Dict[str, Any]]:
    """Get all applications for a user."""
    if not supabase:
        return []

    try:
        user = get_or_create_user(email)
        if not user:
            return []

        response = supabase.table("job_applications").select("*").eq("user_id", user["id"]).order("applied_at", desc=True).execute()
        
        # Ensure we return a list
        if response.data is None:
            return []
        if isinstance(response.data, list):
            return response.data
        return []
    except Exception as e:
        print(f"Error getting applications: {e}")
        return []

def delete_application(app_id: str) -> bool:
    """Delete a job application."""
    if not supabase:
        return False
    
    try:
        response = supabase.table("job_applications").delete().eq("id", app_id).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error deleting application: {e}")
        return False

def save_email_settings(email: str, imap_password: str) -> bool:
    """Save Gmail IMAP password for user."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(email)
        if not user:
            return False
        
        response = supabase.table("users").update({"imap_password": imap_password}).eq("email", email).execute()
        
        # Update all Pending jobs to Tracking
        supabase.table("job_applications").update({"status": "Tracking"}).eq("user_id", user["id"]).eq("status", "Pending").execute()
        
        return response.data is not None
    except Exception as e:
        print(f"Error saving email settings: {e}")
        return False

def delete_user(email: str) -> bool:
    """Delete user and all associated data."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(email)
        if not user:
            return False
        
        # Delete applications first (foreign key)
        supabase.table("job_applications").delete().eq("user_id", user["id"]).execute()
        
        # Delete user
        response = supabase.table("users").delete().eq("email", email).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def reset_tracking(email: str) -> bool:
    """Reset Gmail tracking for user."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(email)
        if not user:
            return False
        
        # Clear password
        supabase.table("users").update({"imap_password": None}).eq("email", email).execute()
        
        # Reset jobs to Pending
        supabase.table("job_applications").update({
            "status": "Pending",
            "gmail_message_id": None
        }).eq("user_id", user["id"]).execute()
        
        return True
    except Exception as e:
        print(f"Error resetting tracking: {e}")
        return False

def has_email_password(email: str) -> bool:
    """Check if user has Gmail password set."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(email)
        if not user:
            return False
        
        return bool(user.get("imap_password"))
    except Exception as e:
        print(f"Error checking password: {e}")
        return False

def save_job_lead(user_email: str, company: str, job_title: str,
                  location: Optional[str] = None, job_url: Optional[str] = None,
                  salary_info: Optional[str] = None, job_description: Optional[str] = None) -> bool:
    """Save a job lead."""
    if not supabase:
        return False
    
    try:
        user = get_or_create_user(user_email)
        if not user:
            return False
        
        lead = {
            "user_id": user["id"],
            "company": company or "Unknown",
            "job_title": job_title,
            "location": location or "Remote",
            "job_url": job_url,
            "salary_info": salary_info,
            "job_description": job_description
        }
        
        response = supabase.table("job_leads").insert(lead).execute()
        return response.data is not None
    except Exception as e:
        print(f"Error saving job lead: {e}")
        return False

def get_job_leads(email: str) -> List[Dict[str, Any]]:
    """Get all job leads for a user."""
    if not supabase:
        return []
    
    try:
        user = get_or_create_user(email)
        if not user:
            return []
        
        response = supabase.table("job_leads").select("*").eq("user_id", user["id"]).order("discovered_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting job leads: {e}")
        return []
