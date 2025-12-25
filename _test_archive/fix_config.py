
import sqlite3
import json
import os

DB_PATH = "data/movie.db"
CONFIG_PATH = "data/repo_config.json"

def fix_config():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'").fetchall()]
        conn.close()
        
        print(f"Available tables: {tables}")
        
        target = "movies"
        if "movie_rag" in tables:
            target = "movie_rag"
            
        print(f"Resetting config to: {target}")
        
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"table_name": target}, f)
            
        print("Config reset successful.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_config()
