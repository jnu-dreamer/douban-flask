import requests
from bs4 import BeautifulSoup
import re

def test_premiere_real():
    # To the Wonder (TV Show)
    url = "https://movie.douban.com/subject/36245596/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://movie.douban.com/"
    }
    
    print(f"Fetching Real URL: {url} ...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            
            # Print Title to verify we got the right page
            page_title = soup.find("title").get_text(strip=True)
            print(f"Page Title: {page_title}")
            
            info_div = soup.find("div", id="info")
            if info_div:
                text = info_div.get_text()
                print("-" * 20)
                print("Raw Text in #info (Partial):")
                print(text[:300] + "...") # Print first 300 chars
                print("-" * 20)
                
                detail_year = ""
                # The logic in spider/douban_spider.py
                if "上映日期:" in text or "首播:" in text:
                    y_parts = re.findall(r"(\d{4})", text)
                    if y_parts:
                        detail_year = y_parts[0]
                
                print(f"Extracted Year: '{detail_year}'")
                
                if detail_year == "2024":
                    print("✅ SUCCESS: Correctly extracted 2024 from Real Page.")
                else:
                    print(f"❌ FAILURE: Extracted '{detail_year}', expected '2024'.")
            else:
                print("Error: <div id='info'> not found in response.")
        else:
            print("Failed to fetch.")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_premiere_real()
