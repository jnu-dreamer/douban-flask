import sqlite3
import sys
import time

def check(timeout=30):
    try:
        conn = sqlite3.connect('data/movie.db', timeout=timeout)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables found (Hex):")
        for t in tables:
            name = t[0]
            print(f"Name: '{name}' | Hex: {name.encode('utf-8').hex()} | Len: {len(name)}")
        conn.close()
        return True
    except sqlite3.OperationalError as e:
        print(f"Locked... retrying. {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return True

for i in range(3):
    if check():
        break
    time.sleep(2)
