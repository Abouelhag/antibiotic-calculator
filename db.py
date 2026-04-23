# db.py - Works with both SQLite (local) and PostgreSQL (Render)
import os
import sqlite3
import psycopg2
import psycopg2.extras
import bcrypt

# Get database URL from environment (for Render) or use local SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Return a database connection (PostgreSQL if DATABASE_URL exists, else SQLite)."""
    if DATABASE_URL:
        # Cloud PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL)
        # Return rows as dictionaries
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # Local SQLite connection
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Create users table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(email: str, password: str) -> bool:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if DATABASE_URL:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, hash_password(password))
            )
        else:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(password))
            )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute(
            "SELECT id, email, password_hash, is_premium FROM users WHERE email = %s",
            (email,)
        )
    else:
        cursor.execute(
            "SELECT id, email, password_hash, is_premium FROM users WHERE email = ?",
            (email,)
        )
    user = cursor.fetchone()
    conn.close()
    if user and check_password(password, user['password_hash']):
        return dict(user)
    return None

def upgrade_to_premium(email: str):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    if DATABASE_URL:
        cursor.execute(
            "UPDATE users SET is_premium = TRUE WHERE email = %s",
            (email,)
        )
    else:
        cursor.execute(
            "UPDATE users SET is_premium = 1 WHERE email = ?",
            (email,)
        )
    conn.commit()
    conn.close()
