import sqlite3
import os

DB_PATH = "data/movie.db"

def inspect():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check count of missing years
    count = cur.execute("SELECT count(*) FROM movies WHERE year_release IS NULL OR year_release = ''").fetchone()[0]
    print(f"Total movies with missing year: {count}")
    
    if count > 0:
        print("\nSample records:")
        rows = cur.execute("SELECT cname, info_link, year_release FROM movies WHERE year_release IS NULL OR year_release = '' LIMIT 5").fetchall()
        for r in rows:
            print(f"Title: {r[0]}, Link: {r[1]}, Year: '{r[2]}'")

    conn.close()

if __name__ == "__main__":
    inspect()
