from supabase import create_client

SUPABASE_URL = "https://dbtqvufidyjdhtpmtgvd.supabase.co"
SUPABASE_KEY = "sb_publishable__jnla4vQuVQpiqmv0zUjHw_c2l4mBHG"

def conectar_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = conectar_supabase()
