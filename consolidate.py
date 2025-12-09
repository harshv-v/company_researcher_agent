import os

PROJECT_ROOT = "."

# -------------------------------------------------------------------------
# 1. FIXED TOOLS AGENT (Better Logging)
# -------------------------------------------------------------------------
tools_agent_py = """
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
        self.serper_key = os.getenv("SERPER_API_KEY")
        self.qdrant = QdrantClient(host=config['memory']['qdrant_host'], port=config['memory']['qdrant_port'])

    async def search_web(self, notes: WorkNotesManager, query: str):
        notes.add_note("Tools", f"Searching Web: {query}")
        
        headers = {'X-API-KEY': self.serper_key, 'Content-Type': 'application/json'}
        try:
            # DEBUG LOG
            logger.info(f"Using Serper Key: {self.serper_key[:5]}... calling {config['tools']['serper_api_endpoint']}")
            
            resp = requests.post(
                config['tools']['serper_api_endpoint'], 
                headers=headers, 
                data=json.dumps({"q": query, "num": 3})
            )
            
            if resp.status_code != 200:
                logger.error(f"Serper API Error ({resp.status_code}): {resp.text}")
                return "", []

            data = resp.json()
            
            results = []
            if 'organic' in data:
                for item in data['organic']:
                    snippet = item.get("snippet") or ""
                    title = item.get("title") or ""
                    results.append({"title": title, "snippet": snippet, "link": item.get("link")})

            # Format text for LLM
            evidence_text = "\\n".join([f"[Web - {r['title']}]: {r['snippet']}" for r in results])
            
            return evidence_text, results
            
        except Exception as e:
            logger.error(f"Search Exception: {e}")
            return "", []

    async def recall_memory(self, notes: WorkNotesManager, url: str, query: str):
        col_name = sanitize_url(url)
        
        if not self.qdrant.collection_exists(col_name):
            notes.add_note("Tools", f"No internal memory found for {col_name}")
            return "", []
            
        notes.add_note("Tools", f"Checking Qdrant: {col_name} for '{query}'")
        
        try:
            res = self.qdrant.query(collection_name=col_name, query_text=query, limit=3)
            
            metadata_list = []
            evidence_parts = []
            
            for r in res:
                doc_text = r.metadata.get('document') or r.metadata.get('text')
                evidence_parts.append(f"[Internal Report]: {doc_text}")
                metadata_list.append(r.metadata)

            evidence_text = "\\n".join(evidence_parts)
            return evidence_text, metadata_list
            
        except Exception as e:
            logger.error(f"Qdrant Error: {e}")
            return "", []
"""

# -------------------------------------------------------------------------
# 2. FIXED EVIDENCE AGENT (Robust JSON Parsing)
# -------------------------------------------------------------------------
evidencer_py = """
from openai import OpenAI
import os
import json
from src.utils.utils import load_prompts
from config.logger_config import WorkNotesManager, get_logger

logger = get_logger("evidencer")

class EvidenceAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompts = load_prompts()

    async def analyze(self, wn: WorkNotesManager, query: str, evidence: str):
        wn.add_note("Evidencer", "Auditing gathered evidence...")
        
        if not evidence.strip():
            return {"sufficient": False, "feedback": "Evidence was empty."}

        sys_prompt = self.prompts['gap_analysis'].format(query=query, evidence=evidence)
        
        try:
            res = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": sys_prompt}]
            )
            raw = res.choices[0].message.content
            parsed = json.loads(raw)
            
            # SAFEGUARD: Ensure keys exist
            return {
                "sufficient": parsed.get("sufficient", False),
                "feedback": parsed.get("feedback", "No feedback provided.")
            }
            
        except json.JSONDecodeError:
            logger.error(f"JSON Parse Error. Raw output: {raw}")
            return {"sufficient": False, "feedback": "LLM returned invalid JSON."}
        except Exception as e:
            logger.error(f"Evidencer Crash: {e}")
            return {"sufficient": False, "feedback": f"Agent crashed: {str(e)}"}
"""

# -------------------------------------------------------------------------
# BUILDER
# -------------------------------------------------------------------------
structure = {
    f"{PROJECT_ROOT}/src/agents/common/tools_agent.py": tools_agent_py,
    f"{PROJECT_ROOT}/src/agents/conversation/evidencer.py": evidencer_py,
}

def fix_debug():
    print(f"🛠️ Patching Tools & Evidencer in {PROJECT_ROOT}...")
    for path, content in structure.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
            print(f"   Updated: {path}")
    print("✅ Fixed! Restart server: python main.py")

if __name__ == "__main__":
    fix_debug()