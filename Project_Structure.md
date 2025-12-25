
# 豆瓣电影 RAG 系统 - 项目结构分析报告

## 📂 根目录文件 (核心入口)

| 文件名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `app.py` | **核心** | Flask Web 应用的主程序。负责路由分发、API 接口定义、后台任务调度 (Rebuild RAG)。 |
| `main.py` | **核心** | 命令行爬虫入口。调用 `spider` 模块执行具体的爬取任务 (按标签/分类)。 |
| `batch_crawl.py` | **工具** | 批量爬取工具。支持多线程、多标签并发爬取，调用 `main.py`。 |
| `requirements.txt` | **配置** | Python 依赖包列表。 |
| `README.md` | **文档** | 项目说明文档。 |

---

## 📂 核心模块目录

### 1. `spider/` (爬虫核心)
| 文件名 | 说明 |
| :--- | :--- |
| `douban_spider.py` | **爬虫逻辑类**。包含 `DoubanSpider` 类，负责网络请求、解析 HTML/JSON、反爬处理 (Retry/Delay)。 |

### 2. `storage/` (数据存储)
| 文件名 | 说明 |
| :--- | :--- |
| `repository.py` | **数据仓库类**。包含 `MovieRepository` 类，负责 SQLite 数据库的 CRUD 操作，以及**配置持久化** (读写 `repo_config.json`)。 |

### 3. `analysis/` (AI & 分析)
| 文件名 | 说明 |
| :--- | :--- |
| `vector_service.py` | **向量服务类**。负责调用 LLM 模型生成 Embedding，构建 FAISS 索引，执行语义检索。 |
| `llm_service.py` | **LLM 接口类**。封装了大模型 API (如豆包/DeepSeek)，负责最终的 RAG 问答生成。 |
| `data_analysis.py` | (可选) 传统数据分析逻辑（如生成词云、统计图表数据）。 |

### 4. `utils/` (通用工具)
| 文件名 | 说明 |
| :--- | :--- |
| `logger.py` | **日志模块**。单例模式的日志记录器，强制输出到 `logs/crawler.log`。 |

---

## 📂 资源与配置目录

### 1. `templates/` (前端页面)
| 文件名 | 说明 |
| :--- | :--- |
| `base.html` | 基础模板（导航栏、Footer）。 |
| `index.html` | 首页（搜索入口）。 |
| `admin.html` | **管理后台**。包含爬虫控制、数据源切换、日志监控等核心管理功能。 |
| `analysis.html` | 数据分析面板（图表展示）。 |
| `search.html` | 搜索结果展示页。 |

### 2. `static/` (静态资源)
*   `assets/`: 存放 CSS (如 `custom.css`), JS 脚本, 图片。
*   `dist/`: 三方库 (ECharts, Bootstrap 等)。

### 3. `data/` (数据持久化)
*   `movie.db`: SQLite 数据库文件 (存储电影元数据)。
*   `repo_config.json`: **配置文件** (存储当前选中的数据表名)。
*   `vectors.pkl`: 向量索引缓存文件 (用于加速启动)。

### 4. `logs/` (系统日志)
*   `crawler.log`: 爬虫及系统运行日志 (Admin 界面读取的就是这个文件)。

---

## 📂 归档与测试目录

### `_test_archive/` (测试文件归档)
> **说明**：此文件夹存放所有**非核心**的测试脚本、一次性修复脚本和调试工具。正常运行项目**不需要**理会此文件夹内容。

主要包含：
*   `check_*.py`: 数据库检查脚本。
*   `fix_*.py`: 配置修复或数据清洗脚本。
*   `inspect_*.py`: 调试用的检视脚本。
*   `verify_debug.py`: 调试验证脚本。
*   以及其他历史遗留的测试代码。
