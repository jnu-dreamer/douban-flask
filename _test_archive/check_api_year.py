import requests
import json

def check_api():
    url = "https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%94%B5%E8%A7%86%E5%89%A7&sort=recommend&page_limit=5&page_start=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://movie.douban.com/tag/%E7%94%B5%E8%A7%86%E5%89%A7"
    }
    
    try:
        print(f"Fetching {url} ...")
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        subjects = data.get("subjects", [])
        
        print(f"\nAPI Returned {len(subjects)} items.")
        print("-" * 40)
        
        for i, sub in enumerate(subjects):
            print(f"Item {i+1}:")
            print(f"  Title: {sub.get('title')}")
            print(f"  Year (Raw): '{sub.get('year')}'") # Quote to see empty string
            print(f"  Rate: {sub.get('rate')}")
            print(f"  ID: {sub.get('id')}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_api()
