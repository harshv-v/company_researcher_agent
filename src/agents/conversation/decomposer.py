from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts

class DecomposerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def decompose(self, wn, query, url):
        wn.add_note("Decomposer", "Splitting query...")
        sys = self.prompts['query_decomposer'].format(query=query, url=url)
        res = self.llm.chat(sys, "Decompose", json_mode=True)
        return res.get("sub_queries", [query])

    async def refine(self, wn, original, feedback):
        wn.add_note("Refiner", f"Refining '{original}' due to: {feedback}")
        sys = self.prompts['query_refiner'].format(original=original, feedback=feedback)
        res = self.llm.chat(sys, "Refine", json_mode=True)
        return res.get("refined_queries", [original])