import sqlite3
from typing import Dict, Iterable, List, Sequence, Any, Tuple, Optional

class MovieRepository:
    """SQLite 电影数据管理辅助类."""

    def __init__(self, db_path: str = "data/movie.db", table_name: str = "movies") -> None:
        self.db_path = db_path
        self.table_name = table_name

    def set_table(self, table_name: str) -> None:
        self.table_name = table_name

    def create_table_if_not_exists(self) -> None:
        sql = f"""
        create table if not exists {self.table_name}
        (
            id integer primary key autoincrement,
            info_link text,
            pic_link text,
            cname text,
            score text,
            rated text,
            introduction text,
            year_release text,
            country text,
            category text,
            directors text,
            actors text
        );
        """
        with self._connect() as conn:
            conn.execute(sql)
            conn.commit()

    def clear_table(self) -> None:
        self.create_table_if_not_exists()
        with self._connect() as conn:
            conn.execute(f"delete from {self.table_name}")
            conn.commit()

    def save_all(self, records: Iterable[Dict[str, str]]) -> int:
        records_list: List[Dict[str, str]] = list(records)
        if not records_list:
            return 0

        self.create_table_if_not_exists()
        fields: Sequence[str] = (
            "info_link",
            "pic_link",
            "cname",
            "score",
            "rated",
            "introduction",
            "year_release",
            "country",
            "category",
            "directors",
            "actors",
        )
        placeholders = ",".join(["?"] * len(fields))
        sql = f"insert into {self.table_name} ({','.join(fields)}) values ({placeholders})"
        values = [tuple(record.get(f, "") for f in fields) for record in records_list]

        with self._connect() as conn:
            conn.executemany(sql, values)
            conn.commit()
        return len(records_list)

    # --- 读取方法 (从 app.py 重构而来) ---

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_stats(self) -> Dict[str, Any]:
        """获取看板的汇总统计信息."""
        with self._connect() as conn:
            cur = conn.cursor()
            total = cur.execute(f"select count(*) from {self.table_name}").fetchone()[0] or 0
            avg_score_row = cur.execute(f"select round(avg(score),2) from {self.table_name}").fetchone()
            avg_score = avg_score_row[0] if avg_score_row and avg_score_row[0] else 0
            high_score = cur.execute(f"select count(*) from {self.table_name} where score >= 9.0").fetchone()[0] or 0
            years = cur.execute(f"select count(distinct year_release) from {self.table_name}").fetchone()[0] or 0
            return {
                "total": total,
                "avg_score": avg_score,
                "high_score": high_score,
                "years": years
            }

    def get_paginated_movies(self, page: int, limit: int = 50) -> Tuple[List[Any], int]:
        """获取指定页码的电影及总页数."""
        offset = (page - 1) * limit
        with self._connect() as conn:
            cur = conn.cursor()
            total = cur.execute(f"select count(*) from {self.table_name}").fetchone()[0] or 0
            
            import math
            total_pages = math.ceil(total / limit) if limit > 0 else 1
            if total == 0: total_pages = 1

            rows = cur.execute(f"select * from {self.table_name} limit ? offset ?", (limit, offset)).fetchall()
            return rows, total_pages

    def search_movies(self, keyword: str) -> List[Any]:
        """按标题、演员、导演或类型搜索电影."""
        if not keyword:
            return []
        
        # 1. 动态检查表列名
        with self._connect() as conn:
            columns_info = conn.execute(f"PRAGMA table_info({self.table_name})").fetchall()
            columns = [info[1] for info in columns_info]

        # 2. 构建查询
        search_fields = ["cname", "category"]
        if "actors" in columns:
            search_fields.append("actors")
        if "directors" in columns:
            search_fields.append("directors")
            
        where_clause = " OR ".join([f"{field} LIKE ?" for field in search_fields])
        sql = f"select * from {self.table_name} where {where_clause}"
        
        # 3. 执行
        pattern = f"%{keyword}%"
        args = [pattern] * len(search_fields)
        
        with self._connect() as conn:
             return conn.execute(sql, args).fetchall()

    def get_all_movies(self) -> List[Any]:
        """获取所有电影记录 (例如用于导出)."""
        with self._connect() as conn:
            return conn.execute(f"select * from {self.table_name}").fetchall()

    def get_score_distribution(self) -> Tuple[List[str], List[int]]:
        """获取电影评分分布."""
        with self._connect() as conn:
            data = conn.execute(f"select score, count(score) from {self.table_name} group by score order by score").fetchall()
        labels = [str(r[0]) for r in data]
        counts = [r[1] for r in data]
        return labels, counts

    def get_year_distribution(self) -> Tuple[List[str], List[int]]:
        """获取电影上映年份分布."""
        with self._connect() as conn:
            data = conn.execute(f"select year_release, count(year_release) from {self.table_name} group by year_release order by year_release").fetchall()
        labels = [str(r[0]) for r in data]
        counts = [r[1] for r in data]
        return labels, counts

    def get_genre_statistics(self) -> List[Dict[str, Any]]:
        """获取 ECharts 使用的类型统计."""
        with self._connect() as conn:
            rows = conn.execute(f"select category from {self.table_name}").fetchall()
        
        genre_data: Dict[str, int] = {}
        for row in rows:
            if not row[0]: continue
            # Split by space as crawler saves them space-separated
            cats = row[0].split() 
            for c in cats:
                genre_data[c] = genre_data.get(c, 0) + 1
        
        return [{"name": k, "value": v} for k, v in genre_data.items()]

    def get_country_statistics(self) -> Tuple[List[str], List[int]]:
        """获取国家/地区统计."""
        with self._connect() as conn:
            rows = conn.execute(f"select country from {self.table_name}").fetchall()
        
        country_data: Dict[str, int] = {}
        for row in rows:
            if not row[0]: continue
            cts = row[0].split() # 假设为空格分隔
            for c in cts:
                country_data[c] = country_data.get(c, 0) + 1
        
        labels = list(country_data.keys())
        counts = list(country_data.values())
        return labels, counts

    def get_all_category_text(self) -> str:
        """获取所有合并的分类文本 (用于词云)."""
        with self._connect() as conn:
            rows = conn.execute(f"select category from {self.table_name}").fetchall()
        return " ".join([r[0] for r in rows if r[0]])

    def get_all_intro_text(self) -> str:
        """获取所有合并的简介文本 (用于词云)."""
        with self._connect() as conn:
            rows = conn.execute(f"select introduction from {self.table_name}").fetchall()
        return " ".join([r[0] for r in rows if r[0]])


__all__ = ["MovieRepository"]
