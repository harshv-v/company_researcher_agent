import yaml
import re

def load_prompts():
    with open("config/prompts.yaml", "r") as f: return yaml.safe_load(f)

def load_config():
    with open("config/config.yaml", "r") as f: return yaml.safe_load(f)

def sanitize_url(url: str):
    clean = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return re.sub(r'[^a-zA-Z0-9]', '_', clean)[:63]