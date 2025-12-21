# DoubanSpider 代码详解 (`spider/douban_spider.py`)

本文档对 `spider/douban_spider.py` 文件进行逐行、逐函数的深度解析，帮助开发者完全理解爬虫的实现细节。

---

## 1. 导入模块 (Imports)

```python
1: import re
2: import time
3: import urllib.error
4: import urllib.request
5: from typing import Dict, List, Optional
6:
7: from bs4 import BeautifulSoup
```

*   **1-4行**: 导入 Python 标准库。
    *   `re`: 正则表达式库，用于从复杂的文本中提取年份、国家、评分人数等特定模式的数据。
    *   `time`: 时间库，主要用于 `time.sleep()` 制造延迟，避免爬取太快被封号。
    *   `urllib`: Python 内置的网络请求库。这里用了两个子模块：`error` (处理网络异常) 和 `request` (发送请求)。
*   **5行**: 导入类型提示 (Type Hinting)，`Dict` (字典), `List` (列表), `Optional` (可选)。这有助于 IDE 代码补全和静态检查，虽然 Python 运行时不强制要求。
*   **7行**: 导入 `BeautifulSoup`，这是最强大的 HTML 解析库，用于把杂乱的网页代码转换成可以通过 CSS 选择器查询的树状结构。

---

## 2. 类定义与初始化 (`__init__`)

```python
10: class DoubanSpider:
11:     """豆瓣电影列表爬虫 (支持 Top250 或指定标签)."""
12:
13:     def __init__(self, base_url: str = "https://movie.douban.com/top250", tag: str = "", pages: int = 10, delay: float = 0.0):
```

*   **10行**: 定义类 `DoubanSpider`。
*   **13行**: 构造函数。接收 4 个参数：
    *   `base_url`: 基础网址，默认为 Top 250。
    *   `tag`: 如果指定了标签（如"喜剧"），爬虫会切换模式去爬分类 API。
    *   `pages`: 爬取页数，默认 10 页（Top 250 一共正好 10 页）。
    *   `delay`: 每一页爬完后的暂停秒数，防封禁。

```python
14:         self.base_url = base_url.rstrip("/")
15:         self.tag = tag
16:         if self.tag:
17:             self.base_url = f"https://movie.douban.com/tag/{urllib.request.quote(self.tag)}"
```

*   **14行**: 去除 URL 末尾的斜杠，防止拼接链接时出现 `//`。
*   **16-17行**: **关键判断**。如果用户传入了 `tag`，说明不是爬 Top250，而是要爬分类电影。这里利用 `urllib.request.quote` 对中文进行 URL 编码（例如 "喜剧" 会变成 `%E5%96%9C%E5%89%A7`），并更新 `base_url`。

```python
21:         self.headers = {
22:             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
23:         }
```

*   **21-23行**: **反爬虫核心**。设置 HTTP 请求头中的 `User-Agent`。
    *   如果不设置这个，Python 发出的请求会默认带上 `Python-urllib/3.x`，豆瓣服务器看到这个 User-Agent 会直接返回 403 Forbidden（禁止访问）。
    *   这里伪装成了一个普通的 Chrome 浏览器。

```python
25:         self.rating_count_pattern = re.compile(r"(\d+)\s*人评价")
27:         self.meta_pattern = re.compile(r"(\d{4})\s*/\s*([^/]+)\s*/\s*(.+)")
```

*   **25行**: 预编译正则表达式，提取评分人数。匹配示例："12345 人评价" -> 提取 "12345"。
*   **27行**: 预编译正则表达式，提取元数据。匹配示例："1994 / 美国 / 剧情 犯罪" -> 分别提取 "1994", "美国", "剧情 犯罪"。

---

## 3. 核心调度方法 (`fetch`)

这是外部调用的入口方法，负责循环翻页和调度解析。

```python
29:     def fetch(self, progress_callback=None) -> List[Dict[str, str]]:
32:         for i in range(self.pages):
```

*   **29行**: 定义 `fetch` 方法，可选接收一个进度回调函数。
*   **32行**: 开始循环，从第 0 页爬到第 `pages-1` 页。

```python
36:             start = i * 20 if self.tag else i * 25
37:             if self.tag:
39:                 url = f"https://movie.douban.com/j/search_subjects?type=movie&tag={urllib.request.quote(self.tag)}&sort=recommend&page_limit=20&page_start={start}"
40:                 self.headers.update({"Referer": f"https://movie.douban.com/tag/{urllib.request.quote(self.tag)}"})
41:             else:
43:                 url = f"{self.base_url}?start={start}"
44:                 self.headers.update({"Referer": "https://movie.douban.com/top250"})
```

*   **36行**: 计算每一页的起始偏移量 `start`。
    *   Top 250 每页 25 部电影 (`i * 25`)。
    *   Tag API 每页 20 部电影 (`i * 20`)。
*   **37-40行 (Tag模式)**: 构造豆瓣 AJAX API 的 URL。这是一个 JSON 接口。同时设置 `Referer` 头，进一步伪装成通过浏览器点击访问的。
*   **41-44行 (Top250模式)**: 构造普通的 HTML 页面 URL，例如 `?start=25`。

```python
47:             content = self._get(url)
48:             if not content:
49:                 continue
```

*   **47行**: 调用 `_get` 辅助方法下载网页内容。
*   **48-49行**: 如果下载失败（返回空字符串），跳过当前页，继续下一页。不会让整个程序崩溃。

```python
51:             if self.tag:
52:                 records.extend(self._parse_json(content))
53:             else:
54:                 records.extend(self._parse(content))
```

*   **51-54行**: **分流处理**。
    *   即如果是 JSON 数据（Tag模式），调用 `_parse_json`。
    *   即如果是 HTML 网页（Top250模式），调用 `_parse`。
    *   `extend` 将解析出的电影列表追加到总结果 `records` 中。

```python
56:             if self.delay:
57:                 time.sleep(self.delay)
```

*   **56-57行**: 每一页爬取完毕后，强制暂停 `delay` 秒。这是礼貌爬取，也是为了防止 IP 被封。

---

## 4. 网络请求方法 (`_get`)

```python
60:     def _get(self, url: str) -> str:
61:         request = urllib.request.Request(url, headers=self.headers)
62:         try:
63:             with urllib.request.urlopen(request) as resp:
64:                 return resp.read().decode("utf-8")
65:         except urllib.error.URLError as e:
                # ... 打印错误 ...
69:             return ""
```

*   **61行**: 构造请求对象，把之前设置好的 `Headers`（包含 User-Agent）带上。
*   **63行**: `urlopen` 发送网络请求。`with` 语句确保请求结束后连接自动关闭。
*   **64行**: 读取二进制响应内容，并用 `utf-8` 解码成字符串。
*   **65-69行**: 捕获所有网络异常（如 404, 403, 超时）。发生异常时打印错误原因并返回空字符串。

---

## 5. JSON 解析逻辑 (`_parse_json`)

这个方法处理 API 返回的数据，并且会**二次发起请求**抓取详情页（因为 API 返回的信息不全）。

```python
71:     def _parse_json(self, json_str: str) -> List[Dict[str, str]]:
75:             data = json.loads(json_str)
76:             subjects = data.get("subjects", [])
77:             for sub in subjects:
```

*   **72/75行**: 解析 JSON 字符串。
*   **76行**: 提取 `subjects` 列表，这是存放电影信息的数组。

```python
92:                 if info_link:
93:                     try:
94:                         time.sleep(1.0) # Be nice
95:                         detail_html = self._get(info_link)
```

*   **92-95行**: **关键点**。API 给的数据仅仅包含片名和分数，没有导演、简介等深度信息。所以这里获取详情页 URL (`info_link`)，**再次调用 `_get` 下载详情页 HTML**。这里还手动 `sleep(1.0)` 以防止频繁访问详情页触发风控。

```python
97:                             detail_soup = BeautifulSoup(detail_html, "html.parser")
```

*   **97行**: 将详情页 HTML 转为 BeautifulSoup 对象。

接下来的 **100-144行** 都是在详情页里“挖”数据：
*   **简介**: 找 `div class="related-info"` 下的 `span property="v:summary"`。
*   **国家/年份**: 找 `div id="info"`，通过字符串分割关键词“制片国家/地区:”和“上映日期:”。
*   **评价人数**: 找 `span property="v:votes"`。
*   **类型**: 找所有 `span property="v:genre"` 并拼接。
*   **导演和演员**: 找 `rel="v:directedBy"` 和 `rel="v:starring"` 的链接文本。为了数据简洁，只取了前 5 位演员。

---

## 6. HTML 解析逻辑 (`_parse`)

这个方法处理 Top 250 这种传统网页。

```python
165:     def _parse(self, html: str) -> List[Dict[str, str]]:
166:         soup = BeautifulSoup(html, "html.parser")
169:         items = soup.find_all("div", class_="item")
```

*   **166行**: 初始化 BeautifulSoup。
*   **169行**: Top 250 页面结构非常规整，每部电影都在一个 `<div class="item">` 里。这里找出所有的电影条目。

```python
170:         for item in items:
171:             link_tag = item.find("a", href=True)
                 # ... 提取链接和海报图片 ...
177:             title_tag = item.find("span", class_="title")
                 # ... 提取中文片名 ...
180:             rating_tag = item.find("span", class_="rating_num")
                 # ... 提取评分 ...
```

*   **170-182行**: 遍历每个电影块，依次查找 `a` 标签（链接）、`img` 标签（图片）、`span class="title"`（片名）、`span class="rating_num"`（评分）。

```python
186:                 m = self.rating_count_pattern.search(star_div.get_text())
187:                 if m:
188:                     rated = m.group(1)
```

*   **186-188行**: 使用之前编译好的正则 `rating_count_pattern` 从文本中筛选出数字。例如文本是 "583920人评价"，`group(1)` 就会拿到 "583920"。

```python
196:             bd_div = item.find("div", class_="bd")
197:             if bd_div:
198:                 p_tag = bd_div.find("p")
205:                     parts = re.split(r"<br\s*/?>", raw_text)
```

*   **196-205行**: 这是 Top 250 页面解析最痛苦的地方。只要电影信息（导演、年份等）全部堆在一个 `<p>` 标签里，中间用 `<br>` 换行。
    *   代码被迫先把这一段转换成字符串，然后用正则 `<br\s*/?>` 把它切成两半。
    *   **前半部分 (parts[0])**: 包含导演和主演。代码继续通过字符串操作 `split("主演:")` 把它们分开。
    *   **后半部分 (parts[1])**: 包含年份、国家、类型。代码使用 `meta_pattern` 正则一次性提取这三个字段。

```python
226:             records.append({ ... })
```

*   **226行**: 将整理好的所有字段打包成一个字典，加入到结果列表中。

---

## 总结

这个文件展示了两种截然不同的爬虫策略：

1.  **基于结构化页面的静态爬取 (`_parse`)**: 依赖 HTML 结构（`div`, `span`, class名）。速度快，但如果网页改版代码就失效了。
2.  **基于 API + 详情页的混合爬取 (`_parse_json`)**: 先从接口拿 ID，再去拿详情。数据更全，适应性更强，但速度慢（因为多了一次 HTTP 请求）且容易触发反爬（需要在中间加 `sleep`）。
