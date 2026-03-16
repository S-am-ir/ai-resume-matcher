import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    # Priority: SUPABASE_DB_URL > DATABASE_URL (Railway) > empty
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or ""
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    MCP_JOBS_HOST: str = os.getenv("MCP_JOBS_HOST", "127.0.0.1")
    MCP_JOBS_PORT: int = int(os.getenv("MCP_JOBS_PORT", 8005))

    class Config:
        env_file = ".env"

settings = Settings()
