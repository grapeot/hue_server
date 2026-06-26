import logging

from fastapi import APIRouter, Query
from models.schemas import ActionResult, RinnaiStatus
from services.rinnai_service import rinnai_service
from services.post_action_collector import schedule_collection

router = APIRouter(prefix="/api/rinnai", tags=["rinnai"])
logger = logging.getLogger(__name__)

@router.get("/status", response_model=RinnaiStatus, summary="Get Rinnai water heater status")
async def get_rinnai_status(refresh: bool = False):
    return await rinnai_service.get_status(trigger_maintenance=refresh)

@router.get("/maintenance", response_model=RinnaiStatus, summary="Trigger Rinnai maintenance refresh")
async def refresh_rinnai_status(wait_seconds: float = Query(5.0, ge=0, le=30)):
    try:
        return await rinnai_service.trigger_maintenance_retrieval(wait_seconds=wait_seconds)
    except Exception as exc:
        logger.exception("Rinnai maintenance refresh failed")
        return {
            "status": "error",
            "message": f"Maintenance refresh failed: {exc}",
            "is_online": False,
        }

@router.get("/circulate", response_model=ActionResult, summary="Start Rinnai recirculation")
async def rinnai_circulate(duration: int = Query(5, gt=0, le=60)):
    result = await rinnai_service.start_circulation(duration)
    await schedule_collection("rinnai", "main_house")
    return result

@router.get("/schedules", response_model=list[dict], summary="List Rinnai schedules")
async def get_rinnai_schedules():
    return await rinnai_service.get_schedules()
