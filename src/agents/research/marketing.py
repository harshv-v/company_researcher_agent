from src.agents.common.tools_agent import ToolsAgent
from src.utils.llm_client import LLMClient

class BaseResearcher:
    def __init__(self, role):
        self.role = role
        self.tools = ToolsAgent()
        self.llm = LLMClient()

    async def execute(self, wn, queries):
        wn.add_note(self.role, f"Running {len(queries)} queries...")
        data = []
        for q in queries:
            text, _ = await self.tools.search_web(wn, q)
            if text: data.append(text)
        return "\n".join(data)