import sqlite3
import os

# Railway ephemeral filesystems will wipe the database on each deploy 
# unless we use a persistent volume. Allow DB path to be set via env var.
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "profiles.db"))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            original_text TEXT,
            parsed_markdown TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_profile(name: str, original_text: str, parsed_markdown: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profiles (name, original_text, parsed_markdown)
        VALUES (?, ?, ?)
    ''', (name, original_text, parsed_markdown))
    profile_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return profile_id

def get_profiles():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM profiles ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "name": row["name"], "created_at": row["created_at"]} for row in rows]

def get_profile_by_id(profile_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_profile(profile_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE profiles SET name = ? WHERE id = ?', (name, profile_id))
    conn.commit()
    conn.close()

def delete_profile(profile_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM profiles WHERE id = ?', (profile_id,))
    conn.commit()
    conn.close()
