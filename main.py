from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from phue import Bridge
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = FastAPI(title="Hue Control API")

# 全局变量存储Bridge实例
bridge = None
light_name = os.getenv("HUE_LIGHT_NAME")

class LightState(BaseModel):
    on: bool
    bri: int = 254  # 默认最大亮度

async def turn_off_light_after_delay(light_name: str, minutes: float):
    """在指定分钟数后关闭灯"""
    try:
        await asyncio.sleep(minutes * 60)  # 转换为秒
        if bridge:
            # 获取灯的ID
            light_id = None
            for l in bridge.lights:
                if l.name == light_name:
                    light_id = l.light_id
                    break
            
            if light_id:
                bridge.set_light(light_id, 'on', False)
                logger.info(f"Light {light_name} turned off after {minutes} minutes")
            else:
                logger.error(f"Light {light_name} not found")
    except Exception as e:
        logger.error(f"Error turning off light: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """启动时初始化Bridge连接"""
    global bridge
    try:
        bridge_ip = os.getenv("HUE_BRIDGE_IP")
        if not bridge_ip:
            logger.error("HUE_BRIDGE_IP not set in environment variables")
            return
        
        bridge = Bridge(bridge_ip)
        # 首次运行时需要按下Bridge上的按钮
        bridge.connect()
        logger.info("Successfully connected to Hue Bridge")
    except Exception as e:
        logger.error(f"Error connecting to Hue Bridge: {str(e)}")

@app.get("/light/{minutes}")
async def control_light(minutes: float):
    """
    打开灯并在指定分钟数后关闭
    如果minutes为0，则立即关闭
    """
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    if minutes < 0:
        raise HTTPException(status_code=400, detail="Minutes must be greater than or equal to 0")
    
    try:
        # 获取灯的ID
        light_id = None
        for l in bridge.lights:
            if l.name == light_name:
                light_id = l.light_id
                break
        
        if not light_id:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        if minutes == 0:
            # 立即关闭
            bridge.set_light(light_id, 'on', False)
            return {
                "status": "success",
                "message": "Light turned off immediately",
                "light_name": light_name,
                "turn_off_time": datetime.now().isoformat()
            }
        else:
            # 打开灯并设置延时关闭
            bridge.set_light(light_id, 'on', True)
            bridge.set_light(light_id, 'bri', 254)  # 设置亮度为最大
            
            # 启动异步任务在指定时间后关闭灯
            asyncio.create_task(turn_off_light_after_delay(light_name, minutes))
            
            return {
                "status": "success",
                "message": f"Light turned on and will turn off in {minutes} minutes",
                "light_name": light_name,
                "turn_on_time": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error controlling light: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取灯的当前状态"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    try:
        light_id = None
        for l in bridge.lights:
            if l.name == light_name:
                light_id = l.light_id
                break
        
        if not light_id:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        light = bridge.get_light(light_id)
        return {
            "name": light_name,
            "state": light["state"]
        }
    except Exception as e:
        logger.error(f"Error getting light status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state")
async def set_state(state: LightState):
    """设置灯的状态"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not connected")
    
    try:
        light_id = None
        for l in bridge.lights:
            if l.name == light_name:
                light_id = l.light_id
                break
        
        if not light_id:
            raise HTTPException(status_code=404, detail=f"Light {light_name} not found")
        
        # 设置灯的状态
        bridge.set_light(light_id, {
            'on': state.on,
            'bri': state.bri
        })
        
        return {
            "status": "success",
            "message": "Light state updated",
            "light_name": light_name,
            "new_state": {
                "on": state.on,
                "bri": state.bri
            }
        }
    except Exception as e:
        logger.error(f"Error setting light state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 