import sqlite3
import datetime
import hashlib
from js import console, navigator

DB_FILE = "upload_logs.db"

def init_db():
    """Initializes the SQLite database and creates the uploads table if it doesn't exist."""
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY,
                upload_timestamp_utc TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                file_name TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                file_hash_sha256 TEXT NOT NULL
            )
        ''')
        con.commit()
        con.close()
        console.log(f"Database '{DB_FILE}' initialized successfully.")
    except Exception as e:
        console.error(f"Error initializing database: {e}")

def get_file_hash(file_content_bytes: bytes) -> str:
    """Calculates the SHA256 hash of the file content."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content_bytes)
    return sha256_hash.hexdigest()

def log_upload(file_name: str, file_size: int, file_content_bytes: bytes):
    """
    Creates a log entry for a file upload and saves it to the SQLite database.

    In a real server-side application, this function would typically write
    to a log file or a database for persistent storage. Since this application
    runs entirely in the browser using PyScript, we log to an in-browser SQLite DB.

    Args:
        file_name (str): The name of the uploaded file.
        file_size (int): The size of the uploaded file in bytes.
        file_content_bytes (bytes): The content of the file as bytes for hashing.
    """
    try:
        user_agent = navigator.userAgent
    except Exception:
        user_agent = "N/A"

    log_entry = {
        "upload_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ip_address": "N/A (client-side operation)",
        "user_agent": user_agent,
        "file_name": file_name,
        "file_size_bytes": file_size,
        "file_hash_sha256": get_file_hash(file_content_bytes),
    }

    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO uploads (
                upload_timestamp_utc, ip_address, user_agent, file_name,
                file_size_bytes, file_hash_sha256
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                log_entry["upload_timestamp_utc"],
                log_entry["ip_address"],
                log_entry["user_agent"],
                log_entry["file_name"],
                log_entry["file_size_bytes"],
                log_entry["file_hash_sha256"],
            ),
        )
        con.commit()
        con.close()
        console.log("File upload logged to SQLite:", log_entry)
    except Exception as e:
        console.error(f"Error logging upload to SQLite: {e}")

    return log_entry
