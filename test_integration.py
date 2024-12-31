import requests
import time
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def save_light_state() -> Dict[str, Any]:
    """保存当前灯的状态"""
    response = requests.get(f"{BASE_URL}/status")
    response.raise_for_status()
    return response.json()["state"]

def restore_light_state(state: Dict[str, Any]):
    """恢复灯的状态"""
    response = requests.post(f"{BASE_URL}/state", json={
        "on": state["on"],
        "bri": state["bri"]
    })
    response.raise_for_status()
    return response.json()

def test_light_control():
    """测试灯的控制功能"""
    try:
        # 保存当前状态
        logger.info("Saving current light state...")
        original_state = save_light_state()
        logger.info(f"Original state: {original_state}")

        # 测试立即关闭（0分钟）
        logger.info("Testing immediate turn off...")
        response = requests.get(f"{BASE_URL}/light/0")
        assert response.status_code == 200
        logger.info("Immediate turn off request successful")

        # 等待1秒确保状态已更新
        time.sleep(1)
        
        # 检查灯是否确实关闭
        current_state = save_light_state()
        assert current_state["on"] is False
        logger.info("Immediate turn off verified")

        # 测试2秒后关闭
        logger.info("Testing 2-second delay turn off...")
        response = requests.get(f"{BASE_URL}/light/0.0333")  # 2秒 = 0.0333分钟
        assert response.status_code == 200
        logger.info("Light turned on successfully")

        # 等待1秒检查灯是否打开
        time.sleep(1)
        current_state = save_light_state()
        assert current_state["on"] is True
        assert current_state["bri"] == 254
        logger.info("Light on state verified")

        # 等待2秒检查灯是否关闭
        time.sleep(2)
        current_state = save_light_state()
        assert current_state["on"] is False
        logger.info("Delayed turn off verified")

        # 恢复原始状态
        logger.info("Restoring original state...")
        restore_light_state(original_state)
        
        # 验证状态是否恢复
        final_state = save_light_state()
        assert final_state["on"] == original_state["on"]
        assert final_state["bri"] == original_state["bri"]
        logger.info("State restoration verified")

        logger.info("All tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        # 确保恢复原始状态
        try:
            restore_light_state(original_state)
            logger.info("Original state restored after error")
        except Exception as restore_error:
            logger.error(f"Error restoring state: {str(restore_error)}")
        return False

if __name__ == "__main__":
    test_light_control() 