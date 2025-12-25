import sqlite3
import sys

try:
    conn = sqlite3.connect('data/movie.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found in DB:")
    for t in tables:
        print(f"- {t[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
