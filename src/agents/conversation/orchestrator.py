from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts
from config.logger_config import get_logger
import json

logger = get_logger("orchestrator")

class OrchestratorAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def route(self, wn, query, url):
        wn.add_note("Orchestrator", f"Routing: {query}")
        sys = self.prompts['orchestrator'].format(query=query, url=url)
        try:
            return self.llm.chat(sys, query, json_mode=True)
        except Exception as e:
            logger.error(f"Orchestrator Error: {e}")
            return {"decision": "RECALL", "query": query, "thought": "Fallback error"}