# 🎬 豆瓣电影数据可视分析系统 | Douban Data Viz

> **本项目**是一个基于 Python Flask 全栈开发的电影数据爬取与可视化分析平台。旨在通过完整的数据工程流程（爬取 -> 存储 -> 分析 -> 展示），帮助开发者理解现代 Web 应用的数据流转与架构设计。

---

## 🏗️ 项目架构剖析 (Architecture Analysis)

本项目采用了经典的 **MVC (Model-View-Controller)** 设计模式的变体，将系统解耦为数据获取层、业务逻辑层和表现层。

### 1. 数据获取层 (Data Ingestion)
- **核心组件**: `spider/douban_spider.py`
- **实现原理**: 
    - 使用 `urllib.request` 发送伪装请求（User-Agent 模拟）。
    - 结合 `BeautifulSoup4` 解析 DOM 树，提取电影元数据（导演、主演、评分等）。
    - 针对 Top250 和 Tag 分类采用不同的 API 策略（分页爬取 vs JSON 接口），实现了对豆瓣反爬机制的初步规避（随机延迟）。

### 2. 数据持久化层 (Persistence)
- **核心组件**: `storage/repository.py`
- **实现原理**:
    - 采用 **SQLite** 轻量级数据库，无需额外部署服务器。
    - 封装了 `MovieRepository` 类，实现了 **DAO (Data Access Object)** 模式。
    - 提供了即时的数据 CRUD 接口，支持动态建表、数据清洗与批量插入。

### 3. Web 服务层 (Service & Controller)
- **核心组件**: `app.py`
- **实现原理**:
    - 基于 **Flask** 框架构建 RESTful 风格的路由。
    - 实现了基础的 **RBAC 权限控制**（简易版），通过装饰器 `@login_required` 保护管理后台。
    - 后端直接处理 Pandas/Numpy 数据聚合逻辑，为前端提供清洗后的 JSON 数据接口。

### 4. 数据可视化层 (Visualization)
- **核心组件**: `templates/analysis.html`, `static/js`
- **实现原理**:
    - 深度集成 **ECharts 5.0**，实现响应式图表渲染。
    - **词云生成**: 结合 `jieba` 分词与 `WordCloud` 库，动态分析电影简介与类型的语义权重。
    - 前后端分离的数据交互：前端通过 AJAX 异步请求后端 API，实现无刷新图表更新。

---

## 🧩 核心功能模块

| 模块名称 | 功能描述 | 技术关键词 |
| :--- | :--- | :--- |
| **数据大屏** | 多维度分析电影分布（类型、产地、年代） | ECharts, Pandas |
| **智能爬虫** | 支持 Top250 榜单与自定义标签（如“科幻”）抓取 | BS4, Multithreading |
| **全文检索** | 对数据库百万级字符进行模糊匹配搜索 | SQL Like, Jinja2 |
| **语义分析** | 对剧情简介进行分词并生成词云画像 | Jieba, WordCloud |
| **后台管理** | 可视化控制爬虫启停、进度监控与数据源切换 | Ajax Polling, Session |

---

## 🛠️ 技术栈 (Tech Stack)

*   **Language**: Python 3.8+
*   **Web Framework**: Flask (Jinja2)
*   **Database**: SQLite3
*   **Crawler**: XML/HTML Parser (BeautifulSoup4)
*   **Visualization**: ECharts, WordCloud
*   **Frontend**: Bootstrap 5, jQuery (Minimal)
*   **Data Analysis**: Numpy, Pandas (Basic)

---

## 🚀 快速启动

1.  **安装依赖环境**
    ```bash
    pip install -r requirements.txt
    ```

2.  **获取初始数据**
    ```bash
    # 爬取 Top 250 数据
    python main.py
    ```

3.  **启动可视化服务**
    ```bash
    python app.py
    ```
    访问 [http://127.0.0.1:5000](http://127.0.0.1:5000) 即可查看大屏。

---

## 📂 项目目录规约

```text
douban_flask/
├── app.py              # Web 应用入口 (Controller)
├── main.py             # 爬虫任务入口 (CLI)
├── analysis/           # 数据分析算法包
├── spider/             # 爬虫策略实现包
├── storage/            # 数据库操作封装包
├── templates/          # 前端视图模板 (View)
└── static/             # 静态资源 (CSS/JS/Images)
```

---

