import json
from fastapi import APIRouter
from models.database import get_device_history

router = APIRouter(tags=["history"])

def _ensure_utc_timestamp(ts: str) -> str:
    """SQLite 存的是 UTC 但无时区后缀，补上 Z 让前端正确解析为 UTC"""
    if not ts or ('Z' in ts or '+' in ts):
        return ts
    return ts.replace(' ', 'T', 1) + 'Z'


@router.get("/api/history")
async def get_history(hours: int = 24):
    hours = max(1, min(168, hours))  # 限制 1–168 小时（7 天）
    history = get_device_history(hours=hours)
    
    for record in history:
        if isinstance(record.get('data'), str):
            record['data'] = json.loads(record['data'])
        ts = record.get('timestamp')
        if ts:
            record['timestamp'] = _ensure_utc_timestamp(str(ts))
    
    return history
