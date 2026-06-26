import asyncio
from typing import Dict

from fastapi import APIRouter
from models.schemas import ActionResult, WemoDeviceStatus
from services.wemo_service import wemo_service
from services.post_action_collector import schedule_collection

router = APIRouter(prefix="/api/wemo", tags=["wemo"])

@router.get("/status", response_model=Dict[str, WemoDeviceStatus], summary="Get Wemo switch statuses")
async def get_wemo_status():
    return await asyncio.to_thread(wemo_service.get_all_status)

@router.get("/{device_name}/toggle", response_model=ActionResult, summary="Toggle a Wemo switch")
async def wemo_toggle(device_name: str):
    result = await asyncio.to_thread(wemo_service.toggle, device_name)
    await schedule_collection("wemo", device_name)
    return result

@router.get("/{device_name}/on", response_model=ActionResult, summary="Turn a Wemo switch on")
async def wemo_on(device_name: str):
    result = await asyncio.to_thread(wemo_service.turn_on, device_name)
    await schedule_collection("wemo", device_name)
    return result

@router.get("/{device_name}/off", response_model=ActionResult, summary="Turn a Wemo switch off")
async def wemo_off(device_name: str):
    result = await asyncio.to_thread(wemo_service.turn_off, device_name)
    await schedule_collection("wemo", device_name)
    return result
