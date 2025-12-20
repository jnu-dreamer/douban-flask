import os
import sqlite3
import jieba
import numpy as np
from PIL import Image
from wordcloud import WordCloud

# Configuration
DB_PATH = "data/movie.db"
MASK_PATH = "static/assets/img/tree.jpg"

def debug_wc():
    print(f"--- Debugging Word Cloud ---")
    
    # 1. Check DB Data
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # Check Category Data
        rows = cur.execute("select category from movies").fetchall()
        text_cat = " ".join([r[0] for r in rows if r[0]])
        print(f"Category Text Length: {len(text_cat)}")
        if len(text_cat) < 10:
             print("Warning: Category text is too short!")

        # Check Intro Data
        rows = cur.execute("select introduction from movies").fetchall()
        text_intro = " ".join([r[0] for r in rows if r[0]])
        print(f"Intro Text Length: {len(text_intro)}")
    finally:
        conn.close()

    # 2. Check Mask
    if os.path.exists(MASK_PATH):
        print(f"Mask found at {MASK_PATH}")
        mask = np.array(Image.open(MASK_PATH))
    else:
        print(f"Error: Mask not found at {MASK_PATH}")
        mask = None

    # 3. Check Font
    font_candidates = [
            "/mnt/c/Windows/Fonts/msyh.ttc",   
            "/mnt/c/Windows/Fonts/simhei.ttf", 
            "C:\\Windows\\Fonts\\msyh.ttc", 
            "C:\\Windows\\Fonts\\simhei.ttf",
    ]
    font_path = None
    for f in font_candidates:
        if os.path.exists(f):
            print(f"Found Font: {f}")
            font_path = f
            break
            
    if not font_path:
        print("Error: No Chinese font found!")
        # Fallback to default which won't support Chinese
        font_path = None

    # 4. Generate
    print("Generating WordCloud...")
    try:
        wc = WordCloud(
            background_color='white',
            mask=mask,
            font_path=font_path,
            scale=2
        )
        # Use Category text for test
        cut = jieba.cut(text_cat)
        string = ' '.join(cut)
        wc.generate_from_text(string)
        
        out_file = "static/debug_wc_result.png"
        wc.to_file(out_file)
        print(f"Success! Saved to {out_file}")
    except Exception as e:
        print(f"Generation Failed: {e}")

if __name__ == "__main__":
    debug_wc()
