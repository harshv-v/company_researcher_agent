import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from src.pipeline.research_pipeline import ResearchPipeline
from src.pipeline.chat_pipeline import ChatPipeline

app = FastAPI(title="Bowmen Unified Agent")
researcher = ResearchPipeline()
chatter = ChatPipeline()

class Request(BaseModel):
    url: str
    message: str = ""

@app.post("/research")
async def start_research(req: Request, background_tasks: BackgroundTasks):
    try:
        result = await researcher.run(req.url)
        crawl_id = result.get("tracking_id")
        if crawl_id:
            background_tasks.add_task(researcher.trigger_deep_crawl, req.url, crawl_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(req: Request):
    try:
        return await chatter.run(req.message, req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)