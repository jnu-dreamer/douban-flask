import argparse
import os

from spider.douban_spider import DoubanSpider
from storage.repository import MovieRepository


def ensure_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def run_crawl(
    base_url: str,
    tag: str,
    pages: int,
    delay: float,
    db_path: str,
    clear: bool = True,
    verbose: bool = True,
    progress_callback = None
) -> None:
    spider = DoubanSpider(base_url=base_url, tag=tag, pages=pages, delay=delay)
    movies = spider.fetch(progress_callback)
    if verbose:
        print(f"Fetched {len(movies)} movies from {spider.base_url}")

    ensure_dir(db_path)
    repo = MovieRepository(db_path)
    if clear:
        repo.clear_table()
    else:
        repo.create_table_if_not_exists()
    saved = repo.save_all(movies)
    if verbose:
        print(f"Saved {saved} movies to {db_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="豆瓣电影爬虫工具")
    
    # 模式选择
    parser.add_argument("--type", type=str, choices=["top250", "tag"], default="top250", 
                        help="爬取模式: 'top250' (默认) 或 'tag' (按分类).")
    
    parser.add_argument("--tag", type=str, default="", help="指定电影类型 (当 mode='tag' 时必填), 例如 '喜剧'")
    
    # 通用选项
    parser.add_argument("--pages", type=int, default=10, help="爬取页数 (默认: 10). Top 250共10页.")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔 (秒)")
    parser.add_argument("--db", type=str, default=os.path.join("data", "movie.db"), help="数据库保存路径")
    parser.add_argument("--no-clear", action="store_true", help="保留旧数据 (默认: 每次爬取前清空数据)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # 准备基础URL与模式
    base_url = "https://movie.douban.com/top250"
    tag_arg = ""
    
    if args.type == "tag":
        if not args.tag:
            print("Error: --tag argument is required when type is 'tag'.")
            print("Example: python main.py --type tag --tag 喜剧")
            exit(1)
        # 使用 JSON API, base_url 由 spider 内部处理
        base_url = "JSON_API" 
        tag_arg = args.tag
    elif args.type == "top250":
        pass # 默认模式
        
    print(f"开始爬取... 模式: {args.type}, 页数: {args.pages}")
    
    run_crawl(
        base_url=base_url,
        tag=tag_arg,
        pages=args.pages,
        delay=args.delay,
        db_path=args.db,
        clear=not args.no_clear,
        verbose=True
    )
