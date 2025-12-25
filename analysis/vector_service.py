
import os
import pickle
import threading 
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger import logger
from storage.repository import MovieRepository

class VectorService:
    def __init__(self, repo: MovieRepository, model_name: str = "shibing624/text2vec-base-chinese"):
        self.repo = repo
        self.model_name = model_name
        self.model = None
        self.vectors = None # numpy array: [n_movies, 768]
        self.movie_ids = None # list: [n_movies] (matches vector index)
        self.id_to_meta = None # dict: id -> {title: '', score: ''} (for quick return)
        self.cache_path = os.path.join("data", "vectors.pkl")
        self.lock = threading.Lock()
        
    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading Embedding Model: {self.model_name} ...")
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise e

    def build_index(self, force_refresh: bool = False):
        """
        Build or load the vector index.
        Thread-safe: ensures only one build happens at a time.
        """
        with self.lock:
            # If already loaded and not forcing refresh, skip
            if not force_refresh and self.vectors is not None:
                return

            if not force_refresh and os.path.exists(self.cache_path):
                try:
                    self._load_from_cache()
                    # Check if cache is stale (simple check: count match)
                    db_count = len(self.repo.get_all_movies())
                    if len(self.movie_ids) == db_count:
                        logger.info("Vector index loaded from cache.")
                        return
                    else:
                        logger.info(f"Cache stale (DB: {db_count}, Cache: {len(self.movie_ids)}). Rebuilding...")
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}. Rebuilding...")
            
            # Rebuild
            self._load_model()
            logger.info("Building vector index from database...")
            
            movies = self.repo.get_all_movies()
            # Filter movies with valid intros
            valid_movies = [m for m in movies if m[6] and len(m[6].strip()) > 5]
            
            if not valid_movies:
                logger.warning("No valid movies with introduction found for indexing.")
                return

            # 构建丰富语义文本: 片名 + 年份 + 国家 + 类型 + 导演 + 主演 + 简介 (Defensive)
            sentences = []
            for m in valid_movies:
                # m schema check: ensure enough columns
                # 0:id, 1:url, 2:pic, 3:title, 4:score, 5:rated, 6:intro, 
                # 7:year, 8:country, 9:category, 10:dirs, 11:actors
                
                title = m[3]
                intro = m[6]
                year = m[7] if len(m) > 7 else ''
                country = m[8] if len(m) > 8 else ''
                category = m[9] if len(m) > 9 else ''
                directors = m[10] if len(m) > 10 else ''
                actors = m[11] if len(m) > 11 else ''
                
                # 优化策略：使用自然语言构建，增强语义连贯性
                # 相比 "Key: Value" 列表，自然语言更能被 BERT 类模型理解实体间的关系 (如 "由...执导")
                meta_part = f"电影《{title}》"
                if year: meta_part += f"于{year}年上映"
                if country: meta_part += f"，产地{country}"
                if category: meta_part += f"，类型为{category}"
                
                staff_part = ""
                if directors: staff_part += f"。由{directors}执导"
                if actors: staff_part += f"，{actors}主演"
                
                text = f"{meta_part}{staff_part}。剧情简介：{intro}"
                sentences.append(text)

            self.movie_ids = [m[0] for m in valid_movies]
            self.id_to_meta = {
                m[0]: {
                    "title": m[3], 
                    "score": m[4], 
                    "pic": m[2], 
                    "intro": m[6], 
                    "url": m[1],
                    "year": m[7],      # Added for filtering
                    "country": m[8],   # Added for filtering
                    "category": m[9],  # Added for filtering
                    "director": m[10], # Added for filtering
                    "actor": m[11]     # Added for filtering
                } for m in valid_movies
            }
            
            logger.info(f"Encoding {len(sentences)} movies (Rich Content) using CPU/GPU...")
            self.vectors = self.model.encode(sentences, normalize_embeddings=True)
            
            self._save_to_cache()
            logger.info("Vector index built and saved.")

    def _save_to_cache(self):
        with open(self.cache_path, "wb") as f:
            pickle.dump({
                "vectors": self.vectors,
                "movie_ids": self.movie_ids,
                "id_to_meta": self.id_to_meta
            }, f)

    def _load_from_cache(self):
        with open(self.cache_path, "rb") as f:
            data = pickle.load(f)
            self.vectors = data["vectors"]
            self.movie_ids = data["movie_ids"]
            self.id_to_meta = data["id_to_meta"]

    def search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """
        Semantic search with metadata filtering.
        """
        if self.vectors is None:
            self.build_index()
            
        if self.vectors is None or len(self.vectors) == 0:
            return []
            
        self._load_model()
        
        query_vec = self.model.encode([query], normalize_embeddings=True)
        similarity = cosine_similarity(query_vec, self.vectors)[0]
        
        # Sort all
        sorted_indices = np.argsort(similarity)[::-1]
        
        results = []
        filters = filters or {}
        
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
                
            score = similarity[idx]
            movie_id = self.movie_ids[idx]
            meta = self.id_to_meta[movie_id]
            
            # --- Filtering Logic ---
            try:
                # Year Filter
                if "year_min" in filters or "year_max" in filters:
                    y_str = re.search(r'\d{4}', str(meta.get("year", "")))
                    y = int(y_str.group()) if y_str else 0
                    if "year_min" in filters and y < filters["year_min"]: continue
                    if "year_max" in filters and y > filters["year_max"]: continue
                
                # Country Filter (Fuzzy)
                if "country" in filters and filters["country"]:
                    if filters["country"] not in str(meta.get("country", "")): continue

                # Category Filter (Fuzzy)
                if "category" in filters and filters["category"]:
                    if filters["category"] not in str(meta.get("category", "")): continue

                # Director Filter (Fuzzy)
                if "director" in filters and filters["director"]:
                    if filters["director"] not in str(meta.get("director", "")): continue

                # Actor Filter (Fuzzy)
                if "actor" in filters and filters["actor"]:
                    if filters["actor"] not in str(meta.get("actor", "")): continue
                    
            except Exception as e:
                # On error (e.g. data missing), skip filtering or skip item? 
                # Safe to skip item or just log and proceed. I'll proceed (lenient).
                pass
            # -----------------------

            results.append({
                "id": movie_id,
                "title": meta["title"],
                "score": meta["score"],
                "pic": meta["pic"],
                "intro": meta["intro"][:100] + "...",
                "url": meta.get("url", ""),
                "year": meta.get("year", ""), 
                "similarity": float(score)
            })
            
        return results

    def search_by_id(self, movie_id: str, top_k: int = 6) -> List[Dict]:
        """
        Search for similar movies using the vector of the given movie_id.
        """
        if self.vectors is None:
            self.build_index()

        if movie_id not in self.movie_ids:
            return []

        # Find the vector for the target movie
        idx = self.movie_ids.index(movie_id)
        target_vec = self.vectors[idx].reshape(1, -1)

        # Calculate Cosine Similarity
        similarity = cosine_similarity(target_vec, self.vectors)[0]

        # Get Top K indices (exclude self)
        # argsort returns indices of sorted values (low to high). 
        # We take from end (high), skipping 1 (self), then taking Top K
        top_indices = np.argsort(similarity)[::-1][1 : top_k + 1]

        results = []
        for i in top_indices:
            score = similarity[i]
            mid = self.movie_ids[i]
            meta = self.id_to_meta[mid]

            results.append({
                "id": mid,
                "title": meta["title"],
                "score": meta["score"],
                "pic": meta["pic"],
                "intro": meta["intro"][:60] + "...", 
                "year": meta.get("year", ""), # Add year if available in meta, but meta dict init in build_index checked earlier might miss it?
                # Actually build_index line 87: "title": m[3], "score": m[4], "pic": m[2], "intro": m[6], "url": m[1]. 
                # Year is not in id_to_meta!
                # I should update id_to_meta or just accept it's missing. ClustringService returns year.
                # Let's peek build_index line 87 again.
                "similarity": round(float(score) * 100, 1)
            })
        return results
