from supabase import create_client, Client
from config import settings

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY

# Only create client if URL and key are provided to avoid crash on startup 
# if user hasn't configured it yet
supabase: Client | None = None
if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing. Supabase remote client operations will fail. Proceeding with raw database.")

async def init_db():
    import asyncpg
    db_url = settings.SUPABASE_DB_URL
    if not db_url:
        print("Warning: SUPABASE_DB_URL is missing. Cannot auto-create tables.")
        return

    try:
        conn = await asyncpg.connect(db_url)
        
        # Enable uuid-ossp extension for uuid_generate_v4() if not exists
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

        # Create Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                oauth_token JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                resume_data JSONB
            );
        ''')

        # Create Job Applications table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id),
                company TEXT NOT NULL,
                job_title TEXT NOT NULL,
                job_description TEXT,
                status TEXT DEFAULT 'applied',
                applied_at TIMESTAMPTZ DEFAULT NOW(),
                last_contact TIMESTAMPTZ DEFAULT NOW(),
                tailored_resume_path TEXT,
                agent_notes TEXT,
                gmail_thread_id TEXT
            );
        ''')

        # Create Job Leads table
        await conn.execute('''
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
        ''')

        # Run migrations for existing tables
        await conn.execute('ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS gmail_thread_id TEXT;')
        await conn.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS imap_password TEXT;')
        
        print("Successfully ensured Supabase tables exist.")
        await conn.close()
    except Exception as e:
        print(f"Error initializing Supabase tables: {e}")
