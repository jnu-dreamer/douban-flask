import sys
import subprocess
import argparse
from utils.logger import logger
import concurrent.futures

def run_single_tag(tag, limit_per_tag, sort, delay, table, start):
    """
    单独抓取一个标签的任务函数
    """
    logger.info(f"🚀 开始抓取: {tag} ...")
    cmd = [
        sys.executable, "main.py",
        "--type", "tag",
        "--tag", tag,
        "--limit", str(limit_per_tag),
        "--append", 
        "--sort", sort,
        "--delay", str(delay),
        "--table", table,
        "--start", str(start)
    ]
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✅ 标签 {tag} 抓取完成。")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 抓取标签 {tag} 时出错: {e}")
        return False

def run_batch_crawl(tags, limit_per_tag, sorts, delay, table, start, workers):
    """
    并发调用 main.py 来爬取多个标签，支持多种排序方式混合抓取。
    """
    # 生成所有任务组合 (Tag x Sort)
    tasks = []
    for tag in tags:
        for sort_type in sorts:
            tasks.append((tag, sort_type))
            
    total_tasks = len(tasks)
    logger.info(f"正在使用 {workers} 个并发进程进行抓取，共 {total_tasks} 个子任务 (标签 x 排序)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        # task[0] is tag, task[1] is sort
        futures = {
            executor.submit(
                run_single_tag, 
                task[0], 
                limit_per_tag, 
                task[1], 
                delay, 
                table, 
                start
            ): f"{task[0]}-{task[1]}" for task in tasks
        }
        
        for future in concurrent.futures.as_completed(futures):
            task_name = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"任务 {task_name} 抛出异常: {e}")

def main():
    parser = argparse.ArgumentParser(description="批量抓取多个类型的电影")
    parser.add_argument("--tags", type=str, default="剧情,喜剧,动作,科幻,悬疑,恐怖,爱情,动画,纪录片", 
                        help="以逗号分隔的标签列表")
    parser.add_argument("--limit", type=int, default=100, help="每个标签抓取的数量")
    # 移除 choices 限制，允许输入 "rank,time"
    parser.add_argument("--sort", type=str, default="recommend", 
                        help="排序方式，可多选(逗号分隔): recommend (推荐), rank (高分), time (时间)")
    parser.add_argument("--delay", type=float, default=1.0, help="网络请求延迟 (秒)")
    parser.add_argument("--table", type=str, default="movies", help="保存到的数据库表名")
    parser.add_argument("--start", type=int, default=0, help="起始偏移量")
    parser.add_argument("--workers", type=int, default=1, help="并发数量")
    
    args = parser.parse_args()
    
    tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
    sort_list = [s.strip() for s in args.sort.split(",") if s.strip()]
    
    if not tag_list:
        logger.error("标签列表不能为空")
        return
    if not sort_list:
        logger.error("排序列表不能为空")
        return

    logger.info(f"开启批量抓取任务：共 {len(tag_list)} 个标签 x {len(sort_list)} 种排序，单任务目标 {args.limit} 部，存入 {args.table}。")
    run_batch_crawl(tag_list, args.limit, sort_list, args.delay, args.table, args.start, args.workers)
    logger.info("所有批量抓取任务已结束。")

if __name__ == "__main__":
    main()
