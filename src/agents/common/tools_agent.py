import os
import json
import requests
from qdrant_client import QdrantClient
from src.utils.utils import load_config, sanitize_url
from config.logger_config import get_logger, WorkNotesManager

logger = get_logger("tools")
config = load_config()

class ToolsAgent:
    def __init__(self):
        self.serper_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_API_KEY")
        self.endpoint = config['tools']['serper_api_endpoint']
        
        self.qdrant = QdrantClient(
            host=config['memory']['qdrant_host'], 
            port=config['memory']['qdrant_port']
        )

    async def search_web(self, notes: WorkNotesManager, query: str):
        notes.add_note("Tools", f"Searching Web: {query}")
        
        if not self.serper_key:
            notes.add_note("Tools", "Error: No API Key found.")
            return "", []

        try:
            data = {}
            results = []
            
            # CASE A: SERPAPI (The 7716... key)
            if "serpapi.com" in self.endpoint:
                logger.info(f"Using SerpApi Mode for query: {query}")
                params = {"api_key": self.serper_key, "q": query, "engine": "google"}
                resp = requests.get(self.endpoint, params=params)
                data = resp.json()
                if 'organic_results' in data:
                    for item in data['organic_results'][:5]:
                        results.append({
                            "title": item.get("title"),
                            "snippet": item.get("snippet"),
                            "link": item.get("link")
                        })

            # CASE B: SERPER.DEV (The gl-... key)
            else:
                headers = {'X-API-KEY': self.serper_key, 'Content-Type': 'application/json'}
                resp = requests.post(self.endpoint, headers=headers, data=json.dumps({"q": query, "num": 5}))
                data = resp.json()
                if 'organic' in data:
                    for item in data['organic']:
                        results.append({
                            "title": item.get("title"),
                            "snippet": item.get("snippet"),
                            "link": item.get("link")
                        })

            if not results:
                logger.warning(f"Search returned 0 results.")
                return "", []

            evidence_text = "\n".join([f"[Web - {r['title']}]: {r['snippet']}" for r in results])
            return evidence_text, results
            
        except Exception as e:
            logger.error(f"Search Exception: {e}")
            notes.add_note("Tools", f"Web Search Exception: {e}")
            return "", []

    async def recall_memory(self, notes: WorkNotesManager, url: str, query: str):
        col_name = sanitize_url(url)
        if not self.qdrant.collection_exists(col_name):
            notes.add_note("Tools", f"No internal memory found for {col_name}")
            return "", []
            
        notes.add_note("Tools", f"Checking Qdrant: {col_name}")
        try:
            res = self.qdrant.query(collection_name=col_name, query_text=query, limit=3)
            evidence = []
            meta = []
            for r in res:
                doc = r.metadata.get('document') or r.metadata.get('text')
                if doc:
                    evidence.append(f"[Internal Report]: {doc}")
                    meta.append(r.metadata)
            
            return "\n".join(evidence), meta
        except Exception as e:
            logger.error(f"Qdrant Error: {e}")
            return "", []