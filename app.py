import os
import sqlite3
import threading
from functools import wraps
from io import BytesIO

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
import main
from storage.repository import MovieRepository
from analysis.clustering import ClusteringService
from analysis.graph import GraphService # 新增图谱服务

# ----------------- 配置 -----------------
DB_PATH = os.path.join("data", "movie.db")
app = Flask(__name__)
app.secret_key = "douban_secret_key_123"

# 初始化数据仓库
repo = MovieRepository(DB_PATH)


# ----------------- 认证装饰器 -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ----------------- Web 页面路由 -----------------

@app.route("/")
def index():
    stats = repo.get_stats()
    return render_template("index.html", stats=stats)


@app.route("/index")
def home():
    return index()


@app.route("/movie")
def movie():
    page = int(request.args.get("page", 1))
    limit = 50
    movies, total_pages = repo.get_paginated_movies(page, limit)
    return render_template("movie.html", movies=movies, page=page, total_pages=total_pages)


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    # 1. 获取电影基本信息
    movie = repo.get_movie_by_id(movie_id)
    if not movie:
        return "Movie not found", 404
        
    # 2. 获取相似推荐
    service = ClusteringService(repo)
    recommendations = service.get_similar_movies(movie_id, n_top=6)
    
    return render_template("detail.html", movie=movie, recommendations=recommendations)





@app.route("/word")
def word():
    return render_template("cloud.html")


@app.route("/word/generate")
def word_generate():
    """生成动态词云图片。"""
    try:
        import jieba
        import jieba.analyse
        from wordcloud import WordCloud
        import numpy as np
        from PIL import Image

        # 0. 获取词云类型
        wc_type = request.args.get("type", "category") 
        
        # 1. 加载蒙版图
        img_name = 'tree.jpg' if wc_type == 'category' else 'image.jpg' 
        img_path = os.path.join(app.root_path, 'static', 'assets', 'img', img_name)
        img_array = None
        if os.path.exists(img_path):
            img_array = np.array(Image.open(img_path))
            # 修复 JPG 压缩噪点：将接近白色的像素 (>240) 强制转为纯白 (255)
            img_array[img_array > 240] = 255

        # 2. 确定字体路径
        font_candidates = [
            "/mnt/c/Windows/Fonts/msyh.ttc",   # WSL access to Windows Fonts
            "/mnt/c/Windows/Fonts/simhei.ttf", 
            "msyh.ttc", "simhei.ttf",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        font_path = None
        for f in font_candidates:
            if os.path.exists(f) or (not f.startswith("/") and os.path.exists(os.path.join(app.root_path, f))): 
                 font_path = f
                 break
        
        wc = WordCloud(
            background_color='white',
            mask=img_array,
            font_path=font_path
        )
        
        # 3. 处理文本与生成逻辑
        if wc_type == "intro":
            # 智能提取关键词 (TF-IDF): 专治简介废话
            # topK=300: 提取前300个关键词
            # allowPOS: 只保留名词(n, nz)和动词(v, vn)
            text = repo.get_all_intro_text()
            tags = jieba.analyse.extract_tags(text, topK=300, withWeight=True, allowPOS=('n', 'nz', 'v', 'vn'))
            # 字典 {word: weight} 传入
            wc.generate_from_frequencies(dict(tags))
        else:
            # 默认分类模式: 直接统计频率
            text = repo.get_all_category_text()
            cut = jieba.cut(text)
            string = ' '.join(cut)
            wc.generate_from_text(string)

        # 4. 输出图片
        image = wc.to_image()
        out = BytesIO()
        image.save(out, format='PNG')
        out.seek(0)
        return send_file(out, mimetype='image/png')

    except Exception as e:
        print(f"WordCloud Error: {e}")
        # 返回占位符或错误图片?
        return f"Error generating wordcloud: {e}", 500


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/aboutMe")
def aboutMe():
    return render_template("aboutMe.html")


@app.route("/help")
def help():
    return render_template("help.html")


@app.route("/search")
def search():
    keyword = request.args.get("q", "")
    datalist = repo.search_movies(keyword)
    return render_template("search.html", movies=datalist, keyword=keyword)


@app.route("/analysis")
def analysis():
    # 1. 概览数据
    genre_list = repo.get_genre_statistics()
    country_labels, country_counts = repo.get_country_statistics()
    
    # 2. 评分与年份数据 (合并自 /score)
    score_labels, score_counts = repo.get_score_distribution()
    year_labels, year_counts = repo.get_year_distribution()
    
    return render_template(
        "analysis.html", 
        genre_data=genre_list, 
        country_labels=country_labels, 
        country_counts=country_counts,
        score_labels=score_labels,
        score_counts=score_counts,
        year_labels=year_labels,
        year_counts=year_counts
    )

# 重定向旧路由到新的合并分析页
@app.route("/score")
def score():
    return redirect(url_for('analysis') + '#trends')

@app.route("/cluster")
def cluster_page():
    return redirect(url_for('analysis') + '#ai-hub')


@app.route("/export")
def export_data():
    import openpyxl

    movies = repo.get_all_movies()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "豆瓣电影数据"
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "豆瓣电影数据"
    
    # 表头
    headers = ["ID", "链接", "封面", "片名", "评分", "评价人数", "简介", "年份", "国家/地区", "类型", "导演", "主演"]
    ws.append(headers)
    
    for movie in movies:
        ws.append(movie)
        
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    
    return send_file(out, as_attachment=True, download_name="douban_movies.xlsx")


# ----------------- 认证与管理后台 -----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "douban666":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash("密码错误！", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin():
    status = load_status()
    # 获取当前数据库的所有表名
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name != 'sqlite_sequence'").fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching tables: {e}")
        tables = []
    
    return render_template("admin.html", status=status, current_table=repo.table_name, tables=tables)


@app.route("/api/switch_table", methods=["POST"])
@login_required
def switch_table():
    new_table = request.form.get("table_name")
    if new_table:
        repo.set_table(new_table)
        flash(f"已切换数据源为: {new_table}", "success")
    return redirect(url_for("admin"))


@app.route("/api/rename_table", methods=["POST"])
@login_required
def rename_table():
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    
    if not old_name or not new_name:
        flash("表名不能为空", "danger")
        return redirect(url_for("admin"))
        
    try:
        repo.rename_table(old_name, new_name)
        flash(f"成功将表 {old_name} 重命名为 {new_name}", "success")
    except Exception as e:
        flash(f"重命名失败: {str(e)}", "danger")
        
    return redirect(url_for("admin"))


# ----------------- API 状态与爬虫 -----------------

STATUS_FILE = "data/status.json"
import json

def save_status(status_data):
    try:
        temp_file = STATUS_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f)
        os.replace(temp_file, STATUS_FILE)
    except Exception as e:
        print(f"Status save failed: {e}")

def load_status():
    if not os.path.exists(STATUS_FILE):
        return {"status": "idle", "current": 0, "total": 0, "message": ""}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"status": "idle", "current": 0, "total": 0, "message": ""}

@app.route("/api/progress")
def api_progress():
    return jsonify(load_status())

@app.route("/api/crawl", methods=["POST"])
@login_required
def api_crawl():
    if not os.path.exists("data"):
        os.makedirs("data")

    initial_status = {
        "status": "running",
        "current": 0,
        "total": 0,
        "message": "正在初始化..."
    }
    save_status(initial_status)

    data = request.json
    crawl_type = data.get("crawl_type", "top250")
    tag = data.get("tag", "")
    pages = int(data.get("pages", 1))
    limit = int(data.get("limit", 200)) # 获取 limit
    no_clear = data.get("no_clear", False)
    
    initial_status["total"] = pages
    save_status(initial_status)
    
    # 自动切换到目标表，确保用户看到的是最新爬取的数据
    target_table = "movies"
    if tag and no_clear:
        target_table = f"movies_{tag}"
    repo.set_table(target_table)
    
    base_url = "https://movie.douban.com/top250"
    if crawl_type == "tag":
        base_url = "JSON_API"
    
    def on_progress(current, total):
        status = load_status()
        status["current"] = current
        status["total"] = total
        status["message"] = f"正在爬取第 {current}/{total} 页..."
        save_status(status)

    def task():
        try:
            print(f"Starting Background Crawl: {crawl_type}, Pages: {pages}, Limit: {limit}")
            main.run_crawl(
                base_url=base_url,
                tag=tag,
                pages=pages,
                limit=limit, # 传递 limit
                delay=3.0, # 增加延迟防封 (3秒)
                db_path="data/movie.db",
                clear=not no_clear,
                verbose=False,
                progress_callback=on_progress
            )
            print("Background Crawl Finished Successfully.")
            
            status = load_status()
            status["status"] = "finished"
            status["message"] = "爬取完成！数据已更新。"
            status["current"] = pages
            save_status(status)
            
        except Exception as e:
            print(f"Background Crawl Error: {e}")
            status = load_status()
            status["status"] = "error"
            status["message"] = f"发生错误: {str(e)}"
            save_status(status)

    thread = threading.Thread(target=task)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "success", "message": "爬虫已启动..."})



# ----------------- 聚类路由 -----------------



@app.route("/api/cluster/data")
def clustering_data():
    try:
        k = int(request.args.get("k", 10)) # 默认为 10 类
        # 限制 k 在 2 到 20 之间，防止错误
        k = max(2, min(k, 20))
        
        service = ClusteringService(repo)
        data = service.perform_clustering(n_clusters=k)
        if data is None:
             return jsonify({"error": "数据不足，无法进行聚类分析 (需要剧情简介数据)"}), 400
        return jsonify(data)
    except Exception as e:
        print(f"Clustering Error: {e}")
        return jsonify({"error": str(e)}), 500


# ----------------- 知识图谱路由 -----------------



@app.route("/api/graph/data")
@login_required
def graph_data():
    try:
        # 默认展示 Top 80 人物，防止图太大卡顿
        limit = int(request.args.get("limit", 80))
        service = GraphService(repo)
        data = service.build_graph(limit_nodes=limit)
        return jsonify(data)
    except Exception as e:
        print(f"Graph Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
