from src.utils.llm_client import LLMClient
from src.utils.utils import load_prompts

class AnswerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.prompts = load_prompts()

    async def generate(self, wn, query, evidence):
        wn.add_note("Answer", "Synthesizing...")
        sys = self.prompts['answer_generator'].format(query=query, evidence=evidence)
        res = self.llm.chat(sys, "Answer", json_mode=True)
        return res.get("final_answer", "Error.")