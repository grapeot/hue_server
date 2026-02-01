"""
Wemo设备集成测试
测试真实的Wemo设备控制功能

默认跳过此测试（需要真实的设备和服务器运行）
手动运行: python test/test_wemo_integration.py
"""

import unittest
import requests
import time
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8000"))
BASE_URL = f"http://localhost:{PORT}"

# 默认跳过测试，除非设置环境变量 RUN_WEMO_TESTS=true
SKIP_TESTS = os.getenv("RUN_WEMO_TESTS", "false").lower() != "true"


@unittest.skipIf(SKIP_TESTS, "Wemo integration tests skipped by default. Set RUN_WEMO_TESTS=true to run.")
class TestWemoIntegration(unittest.TestCase):
    """Wemo设备集成测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.device_name = "Bedroom Light"
        logger.info(f"准备测试设备: {self.device_name}")
    
    def test_bedroom_light_control(self):
        """测试Bedroom Light开关控制"""
        try:
            # 1. 获取设备当前状态
            logger.info("获取设备当前状态...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200, "应该能获取设备状态")
            initial_state = response.json()
            logger.info(f"初始状态: {initial_state}")
            
            initial_on = initial_state.get("state") == "on"
            
            # 2. 开启设备
            logger.info("开启设备...")
            response = requests.post(f"{BASE_URL}/wemo/{self.device_name}/on")
            self.assertEqual(response.status_code, 200, "应该能开启设备")
            result = response.json()
            logger.info(f"开启结果: {result}")
            
            # 等待1秒确保状态更新
            time.sleep(1)
            
            # 3. 验证设备已开启
            logger.info("验证设备已开启...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200)
            current_state = response.json()
            logger.info(f"开启后状态: {current_state}")
            self.assertEqual(current_state.get("state"), "on", "设备应该已开启")
            
            # 4. 等待5秒
            logger.info("等待5秒...")
            time.sleep(5)
            
            # 5. 关闭设备
            logger.info("关闭设备...")
            response = requests.post(f"{BASE_URL}/wemo/{self.device_name}/off")
            self.assertEqual(response.status_code, 200, "应该能关闭设备")
            result = response.json()
            logger.info(f"关闭结果: {result}")
            
            # 等待1秒确保状态更新
            time.sleep(1)
            
            # 6. 验证设备已关闭
            logger.info("验证设备已关闭...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200)
            final_state = response.json()
            logger.info(f"关闭后状态: {final_state}")
            self.assertEqual(final_state.get("state"), "off", "设备应该已关闭")
            
            logger.info("测试完成！所有步骤成功执行")
            
        except requests.exceptions.ConnectionError:
            self.fail("无法连接到服务器。请确保服务器正在运行。")
        except Exception as e:
            import traceback
            logger.error(f"测试失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise


if __name__ == "__main__":
    # 如果直接运行此脚本，自动启用测试
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        os.environ["RUN_WEMO_TESTS"] = "true"
        logger.info("手动运行模式：启用Wemo集成测试")
    
    unittest.main()
