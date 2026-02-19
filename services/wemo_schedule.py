"""
Wemo设备定时任务管理系统
使用APScheduler进行任务调度，支持YAML配置文件
"""

import yaml
import logging
import pytz
import os
from typing import Dict, List, Optional
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Pacific timezone
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

class WemoScheduleManager:
    """管理Wemo设备的定时任务，使用APScheduler"""
    
    def __init__(self, config_file: str = "config/wemo_config.yaml"):
        """
        初始化定时任务管理器
        
        Args:
            config_file: YAML配置文件路径（相对于项目根目录）
        """
        self.config_file = config_file
        self.devices: Dict[str, any] = {}  # 存储设备名称到设备对象的映射
        self.scheduler: Optional[BackgroundScheduler] = None
        self.config: Optional[Dict] = None
        
    def register_device(self, name: str, device):
        """
        注册一个Wemo设备
        
        Args:
            name: 设备名称（用于配置文件中的引用）
            device: pywemo设备对象
        """
        self.devices[name.lower()] = device
        logger.info(f"注册设备: {name}")
    
    def load_config(self) -> Optional[Dict]:
        """
        从YAML配置文件加载配置
        
        Returns:
            配置字典，如果加载失败返回None
        """
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_file}")
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"已加载配置文件: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"读取配置文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def execute_task(self, device_name: str, action: str):
        """
        执行一个定时任务
        
        Args:
            device_name: 设备名称
            action: 动作（on或off）
        """
        device_name_lower = device_name.lower()
        
        if device_name_lower not in self.devices:
            logger.error(f"设备未注册: {device_name}")
            return
        
        device = self.devices[device_name_lower]
        
        try:
            if action == 'on':
                device.on()
                logger.info(f"定时任务执行: {device_name} 开启")
            elif action == 'off':
                device.off()
                logger.info(f"定时任务执行: {device_name} 关闭")
        except Exception as e:
            logger.error(f"执行任务时出错 ({device_name} {action}): {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """启动定时任务调度器"""
        if self.scheduler and self.scheduler.running:
            logger.warning("定时任务调度器已在运行")
            return
        
        # 加载配置文件
        self.config = self.load_config()
        
        if not self.config:
            logger.info("没有配置文件，跳过定时任务初始化")
            return
        
        schedule_config = self.config.get('schedule', {})
        tasks = schedule_config.get('tasks', [])
        
        if not tasks:
            logger.info("没有定时任务需要执行")
            return
        
        # 获取时区
        timezone_str = schedule_config.get('timezone', 'Pacific')
        if timezone_str.lower() == 'pacific':
            timezone = PACIFIC_TZ
        elif timezone_str.lower() == 'utc':
            timezone = pytz.UTC
        else:
            timezone = pytz.timezone('America/Los_Angeles')  # 默认Pacific
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(timezone=timezone)
        
        # 添加任务
        for task in tasks:
            try:
                time_str = task.get('time', '')
                device_name = task.get('device', '')
                action = task.get('action', '')
                
                if not all([time_str, device_name, action]):
                    logger.warning(f"任务配置不完整，跳过: {task}")
                    continue
                
                # 解析时间
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
                
                # 创建任务ID
                task_id = f"{device_name}_{action}_{time_str.replace(':', '')}"
                
                # 创建CronTrigger
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute,
                    second=second,
                    timezone=timezone
                )
                
                # 添加任务
                self.scheduler.add_job(
                    func=lambda d=device_name, a=action: self.execute_task(d, a),
                    trigger=trigger,
                    id=task_id,
                    name=f"{device_name} {action} at {time_str}"
                )
                
                logger.info(f"已安排任务: {time_str} {device_name} {action}")
                
            except Exception as e:
                logger.error(f"添加任务时出错: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 启动调度器
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
    
    def stop(self):
        """停止定时任务调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已停止")
    
    def get_scheduled_tasks(self) -> List[Dict]:
        """获取所有已安排的任务信息"""
        if not self.scheduler or not self.scheduler.running:
            return []
        
        tasks = []
        for job in self.scheduler.get_jobs():
            # 从job的name中提取信息
            name_parts = job.name.split()
            if len(name_parts) >= 3:
                device = name_parts[0]
                action = name_parts[1]
                time_str = ' '.join(name_parts[3:]) if len(name_parts) > 3 else ''
                
                tasks.append({
                    'time': time_str,
                    'device': device,
                    'action': action,
                    'timezone': str(self.scheduler.timezone) if self.scheduler.timezone else 'Pacific',
                    'next_run': str(job.next_run_time) if job.next_run_time else 'N/A'
                })
            else:
                tasks.append({
                    'job_id': job.id,
                    'name': job.name,
                    'next_run': str(job.next_run_time) if job.next_run_time else 'N/A'
                })
        
        return tasks
