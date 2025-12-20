import sqlite3
import os

db_path = "data/movie250.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if we have data in movie250
    count250 = cursor.execute("SELECT count(*) FROM movie250").fetchone()[0]
    print(f"Found {count250} rows in 'movie250'. Migrating to 'movies'...")

    # Copy data
    cursor.execute("""
    INSERT INTO movies (id, info_link, pic_link, cname, score, rated, introduction, year_release, country, category, directors, actors)
    SELECT id, info_link, pic_link, cname, score, rated, introduction, year_release, country, category, '', ''
    FROM movie250
    """)
    
    conn.commit()
    print("Migration successful! specific columns 'directors' and 'actors' set to empty strings.")
    
    # Check result
    count_movies = cursor.execute("SELECT count(*) FROM movies").fetchone()[0]
    print(f"New 'movies' table now has {count_movies} rows.")

except Exception as e:
    print(f"Migration failed or already done: {e}")
    conn.rollback()

conn.close()
