from typing import TypedDict, Annotated, Sequence, Any
import operator
from langchain_core.messages import BaseMessage

def add_messages(left: list[BaseMessage], right: list[BaseMessage]) -> list[BaseMessage]:
    """Append messages."""
    return left + right

class AgentState(TypedDict):
    """
    State representing the current working memory of the agent tracking or applying for jobs.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # User context
    user_id: str
    user_email: str
    user_resume_data: dict[str, Any]
    
    # Current active context
    current_job_id: str | None
    job_description: str | None
    current_mode: str  # "search", "tailor", "track"
    
    # Results
    extracted_jobs: list[dict[str, Any]]
    tailored_resume_path: str | None
    email_drafts: list[str]
    errors: list[str]
    match_analysis: dict[str, Any] | None