import uuid
from config.logger_config import WorkNotesManager, get_logger
from src.memory.memory_manager import MemoryManager
from src.agents.research.scout import ScoutAgent
from src.agents.research.strategist import StrategistAgent
from src.agents.research.finance import BaseResearcher
from src.agents.research.writer import WriterAgent
from src.agents.common.crawler_agent import CrawlerAgent

logger = get_logger("research_pipeline")

class ResearchPipeline:
    def __init__(self):
        self.memory = MemoryManager()
        self.scout = ScoutAgent()
        self.strategist = StrategistAgent()
        self.researcher = BaseResearcher("Specialist")
        self.writer = WriterAgent()
        self.crawler = CrawlerAgent()

    async def run(self, url: str):
        crawl_id = str(uuid.uuid4())[:8]
        wn = WorkNotesManager()
        wn.add_note("Pipeline", f"Starting Phase 1 Research: {url} (ID: {crawl_id})")
        
        # 1. Scout
        context = await self.scout.analyze(wn, url)
        
        # 2. Plan
        plan = await self.strategist.plan(wn, context, url)
        
        # 3. Research
        queries = plan.get('finance', []) + plan.get('marketing', [])
        raw_data = await self.researcher.execute(wn, queries[:6])
        
        # 4. Write
        report = await self.writer.write(wn, url, raw_data)
        
        # 5. Ingest Report
        chunks = [report[i:i+800] for i in range(0, len(report), 800)]
        self.memory.save_knowledge(url, chunks, [{"source": "Phase 1 Report", "document": c} for c in chunks])
        wn.add_note("Pipeline", "Report saved to Qdrant.")
        
        return {
            "status": "success",
            "tracking_id": crawl_id,
            "report": report,
            "notes": wn.get_all_notes()
        }

    async def trigger_deep_crawl(self, url: str, crawl_id: str):
        await self.crawler.deep_crawl(url, crawl_id)