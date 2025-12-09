import logging
import os
from typing import List

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("bowmen")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
    logger.addHandler(ch)

def get_logger(name): return logger.getChild(name)

class WorkNotesManager:
    def __init__(self): self._notes = []
    def add_note(self, agent, msg): self._notes.append(f"[{agent}] {msg}")
    def get_all_notes(self): return self._notes