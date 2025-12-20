import sqlite3

db_path = "data/movie250.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def check_table(name):
    try:
        count = cursor.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        first = cursor.execute(f"SELECT cname FROM {name} LIMIT 1").fetchone()
        title = first[0] if first else "None"
        print(f"Table '{name}': {count} rows. First movie: {title}")
    except Exception as e:
        print(f"Table '{name}': Error - {e}")

check_table("movies")
check_table("movie250")

conn.close()
