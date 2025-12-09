from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts
import json

class WriterAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def write(self, wn, url, data):
        wn.add_note("Writer", "Writing Report...")
        return self.llm.chat(self.prompts['writer'].format(url=url, data=json.dumps(data)), "Write")