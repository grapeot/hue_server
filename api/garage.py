from fastapi import APIRouter, Depends, HTTPException, Path
from models.schemas import ApiError, GarageStatus, GarageToggleResponse
from services.auth import require_control_auth
from services.meross_service import meross_service

router = APIRouter(prefix="/api/garage", tags=["garage"])

@router.get("/status", response_model=GarageStatus, summary="Get Meross garage controller status")
async def get_garage_status():
    return {
        "door_count": meross_service.get_door_count(),
        "available": meross_service._connected
    }

async def _toggle_garage(door_index: int):
    door_count = meross_service.get_door_count()
    if door_index < 1 or door_index > door_count:
        raise HTTPException(400, f"door_index must be between 1 and {door_count}")
    return await meross_service.toggle_door(door_index)


@router.post(
    "/{door_index}/toggle",
    response_model=GarageToggleResponse,
    responses={400: {"model": ApiError}},
    summary="Toggle a garage door",
    description="Sensitive physical action. Uses POST only and sends an optional notification when configured.",
    dependencies=[Depends(require_control_auth)],
)
async def garage_toggle(door_index: int = Path(..., ge=1)):
    return await _toggle_garage(door_index)
