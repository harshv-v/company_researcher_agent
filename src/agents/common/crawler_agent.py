import asyncio
import sys
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from markitdown import MarkItDown
from bs4 import BeautifulSoup
from config.logger_config import get_logger
from src.memory.memory_manager import MemoryManager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = get_logger("crawler")

class MockResponse:
    def __init__(self, content: bytes, url: str):
        self.content = content
        self.url = url
        self.headers = {"content-type": "text/html"}
        self.encoding = "utf-8"
        self.status_code = 200
    def iter_content(self, chunk_size=1024):
        for i in range(0, len(self.content), chunk_size): yield self.content[i:i+chunk_size]
    @property
    def text(self): return self.content.decode("utf-8", errors="replace")

class CrawlerAgent:
    def __init__(self, concurrency: int = 5):
        self.concurrency = concurrency
        self.memory = MemoryManager()
        self.md = MarkItDown()
        self.visited = set()
        self.queue = asyncio.Queue()
        self.root_url = ""
        self.crawl_id = ""

    def _clean_html(self, raw_html: str) -> bytes:
        soup = BeautifulSoup(raw_html, 'html.parser')
        for tag in soup(['nav', 'footer', 'header', 'aside', 'script', 'style', 'svg', 'form', 'noscript', 'iframe']):
            tag.decompose()
        # Heuristic cleaning
        noise_keywords = ['menu', 'navigation', 'nav-', 'sidebar', 'footer', 'cookie', 'banner', 'popup']
        for element in soup.find_all(['div', 'section', 'ul']):
            classes = element.get("class", [])
            eid = element.get("id", "")
            if (classes and any(k in str(c).lower() for c in classes for k in noise_keywords)) or                (eid and any(k in str(eid).lower() for k in noise_keywords)):
                element.decompose()
        return str(soup).encode("utf-8")

    async def fetch_page(self, url: str) -> str:
        logger.info(f"🔎 Scout Crawling: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                html = await page.content()
                clean_bytes = self._clean_html(html)
                mock_resp = MockResponse(content=clean_bytes, url=url)
                result = self.md.convert_response(response=mock_resp)
                logger.info(f"✅ Scout Clean Fetch ({len(result.text_content)} chars)")
                return result.text_content[:15000]
            except Exception as e:
                logger.error(f"Scout Failed: {e}")
                return ""
            finally:
                await browser.close()

    async def _crawl_page(self, context, url):
        page = None
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html = await page.content()
            title = await page.title()
            clean_bytes = self._clean_html(html)
            mock_resp = MockResponse(content=clean_bytes, url=url)
            result = self.md.convert_response(response=mock_resp)
            links = await page.eval_on_selector_all("a[href]", "(els) => els.map(l => l.href)")
            return {"url": url, "title": title, "content": result.text_content}, set(links)
        except: return None, set()
        finally:
            if page: await page.close()

    async def _worker(self, context):
        while True:
            try: url = self.queue.get_nowait()
            except asyncio.QueueEmpty: break
            try:
                data, links = await self._crawl_page(context, url)
                if data and len(data['content']) > 200:
                    chunks = [data['content'][i:i+1000] for i in range(0, len(data['content']), 1000)]
                    meta = [{"source": url, "title": data['title'], "crawl_id": self.crawl_id} for _ in chunks]
                    self.memory.save_knowledge(self.root_url, chunks, meta)
                    logger.info(f"💾 Indexed: {url}")
                    base = urlparse(self.root_url).netloc
                    for link in links:
                        parsed = urlparse(link)
                        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.netloc == base and clean not in self.visited:
                            self.visited.add(clean)
                            await self.queue.put(clean)
            except: pass
            finally: self.queue.task_done()

    async def deep_crawl(self, start_url: str, crawl_id: str, max_pages: int = 100):
        self.root_url = start_url
        self.crawl_id = crawl_id
        self.visited.add(start_url)
        await self.queue.put(start_url)
        logger.info(f"🕷️ Starting Deep Crawl: {start_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            contexts = [await browser.new_context() for _ in range(self.concurrency)]
            tasks = [asyncio.create_task(self._worker(ctx)) for ctx in contexts]
            try: await asyncio.wait_for(self.queue.join(), timeout=600)
            except: logger.warning("Crawl Timeout.")
            for t in tasks: t.cancel()