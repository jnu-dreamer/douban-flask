import re
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from bs4 import BeautifulSoup


class DoubanSpider:
    """豆瓣电影列表爬虫 (支持 Top250 或指定标签)."""

    def __init__(self, base_url: str = "https://movie.douban.com/top250", tag: str = "", pages: int = 10, delay: float = 0.0):
        self.base_url = base_url.rstrip("/")
        self.tag = tag
        if self.tag:
            self.base_url = f"https://movie.douban.com/tag/{urllib.request.quote(self.tag)}"
        
        self.pages = pages
        self.delay = delay
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        # 例如: "123456 人评价"
        self.rating_count_pattern = re.compile(r"(\d+)\s*人评价")
        # 例如: "1994 / 美国 / 剧情 犯罪" (Top250 标准格式)
        self.meta_pattern = re.compile(r"(\d{4})\s*/\s*([^/]+)\s*/\s*(.+)")

    def fetch(self, progress_callback=None) -> List[Dict[str, str]]:
        """Fetch pages and return a list of movie dicts."""
        records: List[Dict[str, str]] = []
        for i in range(self.pages):
            if progress_callback:
                progress_callback(i + 1, self.pages)
            
            start = i * 20 if self.tag else i * 25
            if self.tag:
                 # API 使用 page_limit=20
                url = f"https://movie.douban.com/j/search_subjects?type=movie&tag={urllib.request.quote(self.tag)}&sort=recommend&page_limit=20&page_start={start}"
                self.headers.update({"Referer": f"https://movie.douban.com/tag/{urllib.request.quote(self.tag)}"})
            else:
                # Top250 使用 ?start=0
                url = f"{self.base_url}?start={start}"
                self.headers.update({"Referer": "https://movie.douban.com/top250"})

            print(f"Fetching {url} ...")
            content = self._get(url)
            if not content:
                continue
            
            if self.tag:
                records.extend(self._parse_json(content))
            else:
                records.extend(self._parse(content))
                
            if self.delay:
                time.sleep(self.delay)
        return records

    def _get(self, url: str) -> str:
        request = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(request) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            code = getattr(e, "code", "")
            print(f"Request failed ({code}): {reason} for {url}")
            return ""

    def _parse_json(self, json_str: str) -> List[Dict[str, str]]:
        import json
        records: List[Dict[str, str]] = []
        try:
            data = json.loads(json_str)
            subjects = data.get("subjects", [])
            for sub in subjects:
                # API 返回有限字段: rate, title, url, cover, is_new, id
                # 我们将其映射到我们的 schema
                
                info_link = sub.get("url", "")
                
                # 获取详情以补充缺失字段
                detail_rated = ""
                detail_intro = ""
                detail_country = ""
                detail_year = sub.get("year", "") # 后备
                detail_category = ""
                directors_str = "" # 后备
                actors_str = "" # 后备
                
                if info_link:
                    try:
                        time.sleep(1.0) # Be nice
                        detail_html = self._get(info_link)
                        if detail_html:
                            detail_soup = BeautifulSoup(detail_html, "html.parser")
                            
                            # 提取简介
                            related_info = detail_soup.find("div", class_="related-info")
                            if related_info:
                                span = related_info.find("span", property="v:summary")
                                if span:
                                    detail_intro = span.get_text(strip=True)

                            # Extract Meta (Country, Year) from #info
                            info_div = detail_soup.find("div", id="info")
                            if info_div:
                                text = info_div.get_text()
                                # Country (制片国家/地区:)
                                if "制片国家/地区:" in text:
                                    parts = text.split("制片国家/地区:")
                                    if len(parts) > 1:
                                        detail_country = parts[1].split("\n")[0].strip()
                                
                                # Year (if not in JSON)
                                if "上映日期:" in text or "首播:" in text:
                                    y_parts = re.findall(r"(\d{4})", text)
                                    if y_parts:
                                        detail_year = y_parts[0]

                            # 1. 提取评价人数 (v:votes) - 关键字段 "XX人评价"
                            vote_tag = detail_soup.find("span", property="v:votes")
                            detail_rated = vote_tag.get_text(strip=True) if vote_tag else ""

                            # 2. 提取类型 (v:genre) - 关键字段 Analysis/Labels
                            # JSON 只给出搜索标签, 我们需要所有类型 (例如 "剧情 犯罪")
                            genre_tags = detail_soup.find_all("span", property="v:genre")
                            detail_category = " ".join([t.get_text(strip=True) for t in genre_tags])

                            # 3. 提取演职员表 (Directors/Actors) - 如果 JSON 为空则补充
                            # JSON 通常包含这些, 但详情页更权威.
                            # 仅在 JSON 为空或为了完整性时更新.
                            # 导演 (v:directedBy 非标准, 通常解析文本或 rel)
                            # 简单方法: JSON 数据对名字通常没问题, 但如果为空则检查 #info.
                            if not directors_str:
                                bus = detail_soup.find_all("a", rel="v:directedBy")
                                directors_str = " ".join([b.get_text(strip=True) for b in bus])
                            
                            if not actors_str:
                                acts = detail_soup.find_all("a", rel="v:starring")
                                # 限制前5名以避免数据库膨胀
                                actors_str = " ".join([a.get_text(strip=True) for a in acts[:5]])

                    except Exception as e:
                        print(f"Failed to fetch details for {info_link}: {e}")

                records.append({
                    "info_link": info_link,
                    "pic_link": sub.get("cover", ""),
                    "cname": sub.get("title", ""),
                    "score": sub.get("rate", "0"),
                    "rated": detail_rated,  # Use scraped votes
                    "introduction": detail_intro,
                    "year_release": sub.get("year") or detail_year, 
                    "country": detail_country, 
                    "category": detail_category if detail_category else self.tag, # Prefer full genres
                    "directors": directors_str,
                    "actors": actors_str,
                })
        except json.JSONDecodeError:
            print("Failed to decode JSON response")
        return records

    def _parse(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        records: List[Dict[str, str]] = []
        
        items = soup.find_all("div", class_="item")
        for item in items:
            link_tag = item.find("a", href=True)
            info_link = link_tag["href"] if link_tag else ""

            img_tag = item.find("img")
            pic_link = img_tag["src"] if img_tag else ""

            title_tag = item.find("span", class_="title")
            cname = title_tag.get_text(strip=True) if title_tag else ""

            rating_tag = item.find("span", class_="rating_num")
            score = rating_tag.get_text(strip=True) if rating_tag else ""

            rated = ""
            star_div = item.find("div", class_="star")
            if star_div:
                m = self.rating_count_pattern.search(star_div.get_text())
                if m:
                    rated = m.group(1)

            inq_tag = item.find("span", class_="inq")
            introduction = inq_tag.get_text(strip=True) if inq_tag else ""

            year = country = category = ""
            directors = actors = ""
            
            bd_div = item.find("div", class_="bd")
            if bd_div:
                p_tag = bd_div.find("p")
                
                # 健壮的解析逻辑
                if p_tag:
                     # 通常通过 <br> 分隔文本
                    raw_text = str(p_tag)
                    # 简单的通过 <br> 或 <br/> 分割
                    parts = re.split(r"<br\s*/?>", raw_text)
                    if len(parts) >= 1:
                        # 第一部分是 导演/演员
                        # 移除标签
                        line1 = BeautifulSoup(parts[0], "html.parser").get_text(strip=True)
                        if "导演:" in line1:
                            d_parts = line1.split("主演:")
                            directors = d_parts[0].replace("导演:", "").strip()
                            if len(d_parts) > 1:
                                actors = d_parts[1].strip()
                        
                    if len(parts) >= 2:
                        # 第二部分是 Meta 信息
                        line2 = BeautifulSoup(parts[1], "html.parser").get_text(strip=True)
                         # 1994 / US / Crime
                        m = self.meta_pattern.search(line2)
                        if m:
                            year = m.group(1).strip()
                            country = m.group(2).strip()
                            category = m.group(3).strip()

            records.append(
                {
                    "info_link": info_link,
                    "pic_link": pic_link,
                    "cname": cname,
                    "score": score,
                    "rated": rated,
                    "introduction": introduction,
                    "year_release": year,
                    "country": country,
                    "category": category,
                    "directors": directors,
                    "actors": actors,
                }
            )

        return records


__all__ = ["DoubanSpider"]
