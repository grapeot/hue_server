from fastapi import APIRouter
from services.wemo_service import wemo_service

router = APIRouter(prefix="/api/wemo", tags=["wemo"])

@router.get("/status")
async def get_wemo_status():
    return wemo_service.get_all_status()

@router.get("/{device_name}/toggle")
async def wemo_toggle(device_name: str):
    return wemo_service.toggle(device_name)

@router.get("/{device_name}/on")
async def wemo_on(device_name: str):
    return wemo_service.turn_on(device_name)

@router.get("/{device_name}/off")
async def wemo_off(device_name: str):
    return wemo_service.turn_off(device_name)
