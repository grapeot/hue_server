import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from services.hue_service import hue_service
from services.wemo_service import wemo_service
from services.rinnai_service import rinnai_service
from models.database import save_device_state, init_db

logger = logging.getLogger(__name__)

PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

scheduler = AsyncIOScheduler(timezone=PACIFIC_TZ)

async def collect_device_states():
    logger.info("Collecting device states...")
    
    hue_status = hue_service.get_status()
    if "error" not in hue_status:
        save_device_state("hue", "baby_room", {
            "is_on": hue_status.get("is_on"),
            "brightness": hue_status.get("brightness")
        })
    
    wemo_status = wemo_service.get_all_status()
    for name, status in wemo_status.items():
        if "error" not in status:
            save_device_state("wemo", name, {
                "is_on": status.get("is_on")
            })
    
    rinnai_status = await rinnai_service.get_status()
    if "error" not in rinnai_status:
        save_device_state("rinnai", "main_house", {
            "set_temperature": rinnai_status.get("set_temperature"),
            "inlet_temp": rinnai_status.get("inlet_temp"),
            "outlet_temp": rinnai_status.get("outlet_temp"),
            "water_flow": rinnai_status.get("water_flow"),
            "recirculation_enabled": rinnai_status.get("recirculation_enabled")
        })
    
    logger.info("Device states collected")

async def hue_morning_off():
    logger.info("Hue morning off: 08:20")
    hue_service.turn_off()

async def hue_evening_on():
    logger.info("Hue evening on: 20:00")
    hue_service.turn_on(brightness=128)

def init_scheduler():
    init_db()
    
    scheduler.add_job(
        collect_device_states,
        trigger='interval',
        minutes=30,
        id='collect_device_states',
        replace_existing=True
    )
    
    scheduler.add_job(
        hue_morning_off,
        trigger=CronTrigger(hour=8, minute=20, timezone=PACIFIC_TZ),
        id='hue_morning_off',
        replace_existing=True
    )
    
    scheduler.add_job(
        hue_evening_on,
        trigger=CronTrigger(hour=20, minute=0, timezone=PACIFIC_TZ),
        id='hue_evening_on',
        replace_existing=True
    )
    
    logger.info("Scheduler initialized with jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.id}: {job.trigger}")
    
    scheduler.start()
    logger.info("Scheduler started")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
