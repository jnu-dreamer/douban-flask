import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np
from storage.repository import MovieRepository
import re

class ClusteringService:
    def __init__(self, repo: MovieRepository):
        self.repo = repo
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self):
        # 基础中文停用词表
        return set(['的', '了', '和', '是', '就', '都', '而', '及', '与', '在', '这', '那', '有', '也', '很', '啊', '吧'])

    def _clean_text(self, text):
        if not text:
            return ""
        # 移除非中文字符以获得更好的聚类效果
        text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
        words = jieba.cut(text)
        words = jieba.cut(text)
        return " ".join([w for w in words if w not in self.stopwords and len(w) > 1])

    def perform_clustering(self, n_clusters=8):
        # 1. 获取数据
        movies = self.repo.get_all_movies()
        # 过滤掉简介过短的电影
        valid_movies = [m for m in movies if m[6] and len(m[6]) > 10]
        
        if not valid_movies:
            return None

        # 2. 预处理
        corpus = [self._clean_text(m[6]) for m in valid_movies]
        titles = [m[3] for m in valid_movies]
        ids = [m[1] for m in valid_movies] # 假设为链接或ID
        
        # 3. TF-IDF 向量化
        vectorizer = TfidfVectorizer(max_features=100)
        X = vectorizer.fit_transform(corpus)

        # 4. K-Means 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X)

        # 5. PCA 降维 (降至2维以便可视化)
        pca = PCA(n_components=2)
        coords = pca.fit_transform(X.toarray())

        # 6. 格式化输出供 ECharts 使用
        # 结构: [{name: 'Cluster 1', data: [[x, y, title, link], ...]}, ...]
        result = []
        for i in range(n_clusters):
            cluster_points = []
            for j, label in enumerate(labels):
                if label == i:
                    cluster_points.append([
                        round(float(coords[j][0]), 3), # x
                        round(float(coords[j][1]), 3), # y
                        titles[j],                     # title
                        valid_movies[j][1]             # link
                    ])
            result.append({
                "name": f"聚类 {i+1}",
                "data": cluster_points
            })
            
        return result
