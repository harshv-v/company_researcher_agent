from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts

class StrategistAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def plan(self, wn, context, url):
        wn.add_note("Strategist", "Generating Plan...")
        return self.llm.chat(self.prompts['strategist'].format(context=context, url=url), "Plan", json_mode=True)