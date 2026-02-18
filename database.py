import sqlite3

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    code TEXT PRIMARY KEY,
    file_id TEXT
)
""")

conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def add_video(code, file_id):
    cursor.execute("INSERT OR REPLACE INTO videos (code, file_id) VALUES (?, ?)", (code, file_id))
    conn.commit()

def get_video(code):
    cursor.execute("SELECT file_id FROM videos WHERE code=?", (code,))
    return cursor.fetchone()

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()
