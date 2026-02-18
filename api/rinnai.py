import logging

from fastapi import APIRouter
from services.rinnai_service import rinnai_service

router = APIRouter(prefix="/api/rinnai", tags=["rinnai"])
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_rinnai_status(refresh: bool = False):
    return await rinnai_service.get_status(trigger_maintenance=refresh)

@router.get("/maintenance")
async def refresh_rinnai_status(wait_seconds: float = 5.0):
    try:
        return await rinnai_service.trigger_maintenance_retrieval(wait_seconds=wait_seconds)
    except Exception as exc:
        logger.exception("Rinnai maintenance refresh failed")
        return {
            "status": "error",
            "message": f"Maintenance refresh failed: {exc}",
            "is_online": False,
        }

@router.get("/circulate")
async def rinnai_circulate(duration: int = 5):
    return await rinnai_service.start_circulation(duration)

@router.get("/schedules")
async def get_rinnai_schedules():
    return await rinnai_service.get_schedules()
