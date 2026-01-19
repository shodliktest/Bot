# util.py
import os

def safe_remove(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

async def limit_cache(cache: dict, limit: int = 1000, drop: int = 200):
    if len(cache) > limit:
        keys = list(cache.keys())[:drop]
        for k in keys:
            cache.pop(k, None)
