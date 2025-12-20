import sqlite3
import os

# Path to the database
DB_PATH = os.path.join("data", "movie.db")

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    print(f"--- Inspecting: {DB_PATH} ---\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Get Table Name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    if not tables:
        print("No tables found.")
        return

    for table in tables:
        table_name = table[0]
        if table_name == "sqlite_sequence": continue
        
        print(f"\n--- Schema for table '{table_name}' ---")
        
        # 2. Get Schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        headers = [col[1] for col in columns]
        print(f"Columns: {headers}")

        # 3. Get Sample Data
        print(f"\n--- First 5 Rows of '{table_name}' ---")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        
        for row in rows:
            print(row)
            
        # 4. Count
        cursor.execute(f"SELECT count(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\nTotal Records: {count}")

    conn.close()

if __name__ == "__main__":
    inspect()
