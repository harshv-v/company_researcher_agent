from src.utils.llm_client import LLMClient
from src.agents.common.crawler_agent import CrawlerAgent
from src.utils.utils import load_prompts

class ScoutAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.crawler = CrawlerAgent()
        self.prompts = load_prompts()

    async def analyze(self, wn, url):
        wn.add_note("Scout", f"Crawling {url}...")
        text = await self.crawler.fetch_page(url)
        if not text: return "Generic Context (Site Unreachable)"
        return self.llm.chat(self.prompts['scout'].format(text=text[:4000]), "Analyze")