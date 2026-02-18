import json
from fastapi import APIRouter
from models.database import get_device_history

router = APIRouter(tags=["history"])

@router.get("/api/history")
async def get_history(hours: int = 24):
    history = get_device_history(hours=hours)
    
    for record in history:
        if isinstance(record.get('data'), str):
            record['data'] = json.loads(record['data'])
    
    return history
