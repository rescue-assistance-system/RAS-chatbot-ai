from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(supabase_url, supabase_key)
