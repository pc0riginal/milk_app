from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache for milk rate
_milk_rate_cache = {"value": None, "timestamp": None}
CACHE_TTL = 300  # 5 minutes

def get_cached_milk_rate():
    if _milk_rate_cache["value"] is not None:
        if _milk_rate_cache["timestamp"] and (datetime.now() - _milk_rate_cache["timestamp"]).seconds < CACHE_TTL:
            return _milk_rate_cache["value"]
    return None

def set_cached_milk_rate(rate: float):
    _milk_rate_cache["value"] = rate
    _milk_rate_cache["timestamp"] = datetime.now()

def clear_milk_rate_cache():
    _milk_rate_cache["value"] = None
    _milk_rate_cache["timestamp"] = None
