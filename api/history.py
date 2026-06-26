import json
from fastapi import APIRouter, Query
from models.database import get_device_history
from models.schemas import HistoryRecord

router = APIRouter(tags=["history"])

def _ensure_utc_timestamp(ts: str) -> str:
    """SQLite stores UTC timestamps without a suffix; add Z for frontend parsing."""
    if not ts or ('Z' in ts or '+' in ts):
        return ts
    return ts.replace(' ', 'T', 1) + 'Z'


@router.get("/api/history", response_model=list[HistoryRecord], summary="Get recent device history")
async def get_history(hours: int = Query(24, ge=1, le=168)):
    history = get_device_history(hours=hours)
    
    for record in history:
        if isinstance(record.get('data'), str):
            record['data'] = json.loads(record['data'])
        ts = record.get('timestamp')
        if ts:
            record['timestamp'] = _ensure_utc_timestamp(str(ts))
    
    return history
