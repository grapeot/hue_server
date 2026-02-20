import asyncio
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import uvicorn

from api import hue, wemo, rinnai, garage, status, history, cameras, schedule
from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service
from services.meross_service import meross_service
from services.camera_service import camera_service
from services.scheduler import init_scheduler, shutdown_scheduler
from services.wemo_schedule import WemoScheduleManager
from services.action_executor import init_action_executor

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Home Dashboard", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hue.router)
app.include_router(wemo.router)
app.include_router(rinnai.router)
app.include_router(garage.router)
app.include_router(status.router)
app.include_router(history.router)
app.include_router(cameras.router)
app.include_router(schedule.router)

wemo_schedule_manager = None

@app.on_event("startup")
async def startup_event():
    global wemo_schedule_manager
    
    logger.info("Starting Smart Home Dashboard...")
    hue_ip = os.getenv("HUE_BRIDGE_IP")
    logger.info(f"Debug: HUE_BRIDGE_IP={hue_ip or '(未配置)'}, .env exists={Path(__file__).parent.joinpath('.env').exists()}")
    hue_service.connect()
    
    wemo_service.init_devices()
    
    await rinnai_service.connect()
    
    await meross_service.connect()
    
    camera_user = os.getenv("CAMERA_USER")
    camera_password = os.getenv("CAMERA_PASSWORD")
    if camera_user and camera_password:
        camera_service.set_credentials(camera_user, camera_password)
        camera_service.load_config()
    else:
        logger.warning("Camera credentials not configured, camera feature disabled")
    
    init_scheduler()
    
    init_action_executor()
    
    wemo_schedule_manager = WemoScheduleManager("config/wemo_config.yaml")
    for name, device in wemo_service.devices.items():
        wemo_schedule_manager.register_device(name, device)
    wemo_schedule_manager.start()
    
    logger.info("Smart Home Dashboard started")

@app.on_event("shutdown")
async def shutdown_event():
    global wemo_schedule_manager
    
    logger.info("Shutting down Smart Home Dashboard...")
    
    shutdown_scheduler()
    
    if wemo_schedule_manager:
        wemo_schedule_manager.stop()
    
    await camera_service.close()
    
    await rinnai_service.close()
    await meross_service.close()
    
    logger.info("Smart Home Dashboard shutdown complete")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
    
    logger.info(f"Serving frontend from {FRONTEND_DIST}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7999"))
    uvicorn.run(app, host="0.0.0.0", port=port)
