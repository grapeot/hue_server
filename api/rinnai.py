from fastapi import APIRouter
from services.rinnai_service import rinnai_service

router = APIRouter(prefix="/api/rinnai", tags=["rinnai"])

@router.get("/status")
async def get_rinnai_status():
    return await rinnai_service.get_status()

@router.get("/circulate")
async def rinnai_circulate(duration: int = 5):
    return await rinnai_service.start_circulation(duration)

@router.get("/schedules")
async def get_rinnai_schedules():
    return await rinnai_service.get_schedules()
