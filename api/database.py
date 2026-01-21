import os
import libsql_experimental as libsql
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

def get_connection():
    """
    Get a fresh database connection for each request.
    
    In serverless environments (like Vercel), connections can't be 
    cached globally as they expire when functions are paused.
    Each invocation needs its own connection.
    """
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )
