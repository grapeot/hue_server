import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from models.schemas import ApiError, CameraListResponse

from services.camera_service import camera_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("", response_model=CameraListResponse, summary="List configured cameras")
async def get_cameras():
    return {"cameras": camera_service.get_cameras()}


@router.get(
    "/snapshot/{camera_id}",
    responses={
        200: {"content": {"image/jpeg": {}}},
        404: {"model": ApiError},
        502: {"model": ApiError},
        504: {"model": ApiError},
    },
    summary="Fetch a camera snapshot",
)
async def get_snapshot(camera_id: str):
    image_data, error = await camera_service.get_snapshot(camera_id)
    
    if error:
        logger.warning(f"Snapshot error for {camera_id}: {error}")
        if "not found" in error:
            raise HTTPException(status_code=404, detail=error)
        elif "Timeout" in error:
            raise HTTPException(status_code=504, detail=error)
        else:
            raise HTTPException(status_code=502, detail=error)
    
    return Response(content=image_data, media_type="image/jpeg")
