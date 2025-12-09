from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from src.utils.utils import load_config

load_dotenv()
config = load_config()

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Force the model from config
        self.model = config['llm']['model_id']

    def chat(self, sys_prompt, user_content, json_mode=False):
        try:
            res = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"} if json_mode else {"type": "text"},
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_content}],
                temperature=config['llm']['temperature']
            )
            content = res.choices[0].message.content
            return json.loads(content) if json_mode else content
        except Exception as e:
            return {} if json_mode else f"Error: {e}"