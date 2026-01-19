# runtime.py
import asyncio
from typing import Dict, Any

class Runtime:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.loop = None
        self.is_running = False

        # RAM holatlar
        self.user_settings: Dict[int, str] = {}   # chat_id -> "groq" | "local"
        self.user_data: Dict[int, Dict[str, Any]] = {}
        self.tasks: Dict[int, asyncio.Task] = {}
        self.translation_cache: Dict[tuple, str] = {}
        self.logs = []

    def log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.logs.append(line)
        if len(self.logs) > 300:
            self.logs = self.logs[-300:]
