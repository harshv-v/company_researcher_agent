import redis
import json
import os
from qdrant_client import QdrantClient
from src.utils.utils import sanitize_url, load_config

config = load_config()

class MemoryManager:
    def __init__(self):
        try:
            self.redis = redis.Redis(
                host=config['memory']['redis_host'], 
                port=config['memory']['redis_port'], 
                decode_responses=True
            )
            self.redis.ping()
        except:
            print("⚠️ Redis connection failed. Chat history will be ephemeral.")

        self.qdrant = QdrantClient(
            host=config['memory']['qdrant_host'], 
            port=config['memory']['qdrant_port']
        )

    def add_turn(self, url, role, content):
        key = f"chat:{sanitize_url(url)}"
        try:
            self.redis.rpush(key, json.dumps({"role": role, "content": content}))
            self.redis.ltrim(key, -10, -1)
        except: pass

    def get_history(self, url):
        try:
            items = self.redis.lrange(f"chat:{sanitize_url(url)}", 0, -1)
            return [json.loads(i) for i in items]
        except: return []

    def save_knowledge(self, url, text_chunks, metadata_list=None):
        col_name = sanitize_url(url)
        if not self.qdrant.collection_exists(col_name):
            self.qdrant.create_collection(
                collection_name=col_name, 
                vectors_config=self.qdrant.get_fastembed_vector_params()
            )
        
        if metadata_list is None:
            metadata_list = [{"source": "Phase 1 Report"} for _ in text_chunks]

        self.qdrant.add(collection_name=col_name, documents=text_chunks, metadata=metadata_list)

    def recall(self, url, query, top_k=3):
        col_name = sanitize_url(url)
        if not self.qdrant.collection_exists(col_name): return None
        res = self.qdrant.query(collection_name=col_name, query_text=query, limit=top_k)
        if not res: return None
        return "\n".join([f"- {r.metadata.get('document', r.metadata)}" for r in res])