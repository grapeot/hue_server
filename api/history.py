import json
from fastapi import APIRouter
from models.database import get_device_history

router = APIRouter(tags=["history"])

@router.get("/api/history")
async def get_history(hours: int = 24):
    hours = max(1, min(168, hours))  # 限制 1–168 小时（7 天）
    history = get_device_history(hours=hours)
    
    for record in history:
        if isinstance(record.get('data'), str):
            record['data'] = json.loads(record['data'])
    
    return history
