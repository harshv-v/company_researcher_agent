import asyncio
import redis
import json
from config.logger_config import WorkNotesManager, get_logger
from src.utils.utils import load_config, sanitize_url

from src.memory.memory_manager import MemoryManager
from src.agents.common.tools_agent import ToolsAgent
from src.agents.conversation.orchestrator import OrchestratorAgent
from src.agents.conversation.decomposer import DecomposerAgent
from src.agents.conversation.evidencer import EvidenceAgent
from src.agents.conversation.answer import AnswerAgent

logger = get_logger("chat_pipeline")
config = load_config()

class ChatPipeline:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.tools = ToolsAgent()
        self.evidencer = EvidenceAgent()
        self.decomposer = DecomposerAgent()
        self.answer_agent = AnswerAgent()
        self.memory = MemoryManager()
        
        try:
            self.redis = redis.Redis(
                host=config['memory']['redis_host'], 
                port=config['memory']['redis_port'], 
                decode_responses=True
            )
        except: self.redis = None

    async def run(self, message: str, url: str):
        wn = WorkNotesManager()
        wn.add_note("Pipeline", f"Processing: '{message}' for '{url}'")
        
        trace = {"initial_intent": "", "decomposition": [], "execution_steps": []}
        session_key = f"chat:{sanitize_url(url)}"
        
        # 1. Routing
        try:
            route = await self.orchestrator.route(wn, message, url)
            decision = route.get("decision", "CHAT")
            refined_query = route.get("query", message)
        except:
            decision = "CHAT"
            refined_query = message

        trace["initial_intent"] = decision
        wn.add_note("Orchestrator", f"Decision: {decision}")
        
        if decision == "CHAT":
            hist = []
            if self.redis: hist = self.redis.lrange(session_key, 0, 5)
            final_ans = await self.answer_agent.generate(wn, message, f"Chat History: {hist}")
            return {"answer": final_ans, "work_notes": wn.get_all_notes(), "trace": trace}

        # 2. Research Loop
        sub_queries = []
        if decision in ["RECALL", "SEARCH"] and len(refined_query.split()) < 10:
            sub_queries = [refined_query]
        else:
            sub_queries = await self.decomposer.decompose(wn, refined_query, url)
            
        trace["decomposition"] = sub_queries
        collected_evidence = []
        
        for query in sub_queries:
            candidate_queries = [query]
            loops = 0
            is_sufficient = False
            force_web = (decision == "SEARCH")
            
            query_journey = {"original_query": query, "attempts": []}
            
            while loops < config['tools']['max_loops'] and not is_sufficient:
                current_q = candidate_queries[0]
                attempt_log = {"loop": loops+1, "query": current_q}
                wn.add_note("Loop", f"Attempt {loops+1}: {current_q}")
                
                # A. Retrieve
                evidence = ""
                source = "Qdrant"
                meta_data = []
                
                if not force_web:
                    evidence, meta_data = await self.tools.recall_memory(wn, url, current_q)
                    if not evidence:
                        source = "SerpAI (Fallback)"
                        evidence, meta_data = await self.tools.search_web(wn, current_q)
                else:
                    source = "SerpAI (Forced)"
                    evidence, meta_data = await self.tools.search_web(wn, current_q)
                
                attempt_log["source"] = source
                attempt_log["tools_output"] = meta_data
                
                # B. Audit
                audit = await self.evidencer.analyze(wn, message, evidence)
                is_sufficient = audit.get("sufficient", False)
                feedback = audit.get("feedback", "Missing data")
                
                attempt_log["audit_passed"] = is_sufficient
                attempt_log["audit_feedback"] = feedback
                
                if is_sufficient:
                    collected_evidence.append(evidence)
                    wn.add_note("Evidencer", "Evidence Accepted.")
                else:
                    wn.add_note("Evidencer", f"Insufficient: {feedback}")
                    if source == "Qdrant": 
                        force_web = True
                        wn.add_note("Pipeline", "Switching to Web Search for next attempt.")
                    
                    new_qs = await self.decomposer.refine(wn, current_q, feedback)
                    candidate_queries = new_qs 
                    loops += 1
                
                query_journey["attempts"].append(attempt_log)
            
            trace["execution_steps"].append(query_journey)

        # 3. Final Answer
        final_ans = await self.answer_agent.generate(wn, message, "\n".join(collected_evidence))
        
        if self.redis:
            self.redis.rpush(session_key, json.dumps({"role": "user", "content": message}))
            self.redis.rpush(session_key, json.dumps({"role": "assistant", "content": final_ans}))
        
        return {"answer": final_ans, "work_notes": wn.get_all_notes(), "trace": trace}