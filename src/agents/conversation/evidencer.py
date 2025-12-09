from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts
from config.logger_config import get_logger
import json

logger = get_logger("evidencer")

class EvidenceAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def analyze(self, wn, query, evidence):
        wn.add_note("Evidencer", "Auditing...")
        if not evidence or not evidence.strip(): 
            return {"sufficient": False, "feedback": "Evidence Empty."}
        
        sys = self.prompts['gap_analysis'].format(query=query, evidence=evidence)
        try:
            return self.llm.chat(sys, "Audit", json_mode=True)
        except Exception as e:
            logger.error(f"Evidencer Error: {e}")
            return {"sufficient": False, "feedback": "Audit crashed."}