import sqlite3
import os

db_path = "data/movie250.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Inspect columns
    print("\nColumns in 'movie250':")
    cols = cursor.execute("PRAGMA table_info(movie250)").fetchall()
    for col in cols:
        print(col)
        
    print("\nColumns in 'movies':")
    cols = cursor.execute("PRAGMA table_info(movies)").fetchall()
    for col in cols:
        print(col)
    
    conn.close()
