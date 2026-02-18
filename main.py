import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

from api import hue, wemo, rinnai, garage, status, history
from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service
from services.meross_service import meross_service
from services.scheduler import init_scheduler, shutdown_scheduler
from wemo_schedule import WemoScheduleManager

load_dotenv()

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

wemo_schedule_manager = None

@app.on_event("startup")
async def startup_event():
    global wemo_schedule_manager
    
    logger.info("Starting Smart Home Dashboard...")
    
    hue_service.connect()
    
    wemo_service.init_devices()
    
    await rinnai_service.connect()
    
    await meross_service.connect()
    
    init_scheduler()
    
    wemo_schedule_manager = WemoScheduleManager("wemo_config.yaml")
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
    
    await rinnai_service.close()
    await meross_service.close()
    
    logger.info("Smart Home Dashboard shutdown complete")

@app.get("/")
async def root():
    return {
        "name": "Smart Home Dashboard",
        "version": "2.0.0",
        "endpoints": {
            "hue": "/api/hue",
            "wemo": "/api/wemo",
            "rinnai": "/api/rinnai",
            "garage": "/api/garage",
            "status": "/api/status"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
