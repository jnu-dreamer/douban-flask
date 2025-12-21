import urllib.request
import urllib.error

url = "https://movie.douban.com/chart"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

req = urllib.request.Request(url, headers=headers)
try:
    resp = urllib.request.urlopen(req)
    print(resp.read().decode("utf-8"))
except Exception as e:
    print(e)
