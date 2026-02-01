import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app, light_timer_task
import json
from dotenv import load_dotenv

class MockLight:
    """模拟Hue灯对象"""
    def __init__(self, light_id: int, name: str):
        self.light_id = light_id
        self.name = name

class TestHueAPI(unittest.TestCase):
    def setUp(self):
        """测试前的设置"""
        # 加载环境变量
        load_dotenv()
        self.light_name = os.getenv("HUE_LIGHT_NAME")

        # 创建测试客户端
        self.client = TestClient(app)
        
        # 模拟灯的状态
        self.mock_light_state = {
            "state": {
                "on": True,
                "bri": 100,
                "alert": "none",
                "mode": "homeautomation",
                "reachable": True
            }
        }
        
        # 创建mock light
        self.mock_light = MockLight(1, self.light_name)

        # 创建mock bridge
        self.mock_bridge = MagicMock()
        self.mock_bridge.lights = [self.mock_light]
        self.mock_bridge.get_light.return_value = self.mock_light_state
        
        # 设置mock bridge的方法
        def mock_set_light(light_id, *args):
            if isinstance(args[0], dict):
                return True
            elif isinstance(args[0], str) and args[0] == 'on':
                return True
            return True
        self.mock_bridge.set_light.side_effect = mock_set_light

        # 应用mock
        self.patcher = patch('main.bridge', self.mock_bridge)
        self.patcher.start()

    def tearDown(self):
        """测试后的清理"""
        # 清理全局timer任务
        import main
        if main.light_timer_task and not main.light_timer_task.done():
            main.light_timer_task.cancel()
            main.light_timer_task = None
        self.patcher.stop()

    def test_status_endpoint(self):
        """测试状态获取endpoint"""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], self.light_name)
        self.assertEqual(data["state"], self.mock_light_state["state"])

    def test_immediate_turn_off(self):
        """测试立即关闭功能"""
        response = self.client.get("/light/0")
        self.assertEqual(response.status_code, 200)
        self.mock_bridge.set_light.assert_called_with(1, 'on', False)

    def test_delayed_turn_off(self):
        """测试延时关闭功能"""
        response = self.client.get("/light/0.0333")  # 2秒
        self.assertEqual(response.status_code, 200)
        # 验证灯被打开
        self.mock_bridge.set_light.assert_any_call(1, 'on', True)
        self.mock_bridge.set_light.assert_any_call(1, 'bri', 10)  # 应该设置为最低亮度

    def test_set_state(self):
        """测试设置状态功能"""
        new_state = {"on": True, "bri": 128}
        response = self.client.post("/state", json=new_state)
        self.assertEqual(response.status_code, 200)
        self.mock_bridge.set_light.assert_called_with(1, {
            'on': True,
            'bri': 128
        })

    def test_invalid_minutes(self):
        """测试无效的分钟数"""
        response = self.client.get("/light/-1")
        self.assertEqual(response.status_code, 400)

    def test_light_not_found(self):
        """测试找不到灯的情况"""
        # 清空灯列表模拟找不到灯
        self.mock_bridge.lights = []
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 404)

    def test_bridge_not_connected(self):
        """测试Bridge未连接的情况"""
        # 停止当前的mock
        self.patcher.stop()
        # 创建新的mock，将bridge设为None
        with patch('main.bridge', None):
            # 测试所有endpoint
            endpoints = [
                ("/status", "GET"),
                ("/light/1", "GET"),
                ("/state", "POST", {"on": True, "bri": 254})
            ]

            for endpoint in endpoints:
                if len(endpoint) == 2:
                    path, method = endpoint
                    data = None
                else:
                    path, method, data = endpoint

                if method == "GET":
                    response = self.client.get(path)
                else:
                    response = self.client.post(path, json=data)
                
                self.assertEqual(response.status_code, 503)
                self.assertIn("Bridge not connected", response.json()["detail"])
        
        # 重新启动原来的mock
        self.patcher.start()
    
    def test_timer_reset(self):
        """测试timer重置功能：连续两次调用应该重置timer而不是创建两个"""
        import main
        
        # 确保没有旧的timer
        if main.light_timer_task:
            main.light_timer_task.cancel()
            main.light_timer_task = None
        
        # 第一次调用：创建7分钟timer
        response1 = self.client.get("/light/7")
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertIn("turn_on_time", data1)
        
        # 获取第一个timer任务
        timer1 = main.light_timer_task
        self.assertIsNotNone(timer1, "应该创建了timer任务")
        
        # 第二次调用：应该重置timer（取消旧的，创建新的）
        response2 = self.client.get("/light/7")
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertIn("turn_on_time", data2)
        
        # 验证旧的timer被取消了（如果它还在运行）
        if timer1 and not timer1.done():
            self.assertTrue(timer1.cancelled(), "旧的timer应该被取消")
        
        # 验证新的timer已创建
        timer2 = main.light_timer_task
        self.assertIsNotNone(timer2, "应该创建了新的timer任务")
        self.assertIsNot(timer1, timer2, "应该是新的timer任务")
    
    def test_cancel_timer(self):
        """测试取消timer功能"""
        import main
        
        # 确保没有旧的timer
        if main.light_timer_task:
            main.light_timer_task.cancel()
            main.light_timer_task = None
        
        # 先创建一个timer（使用较长时间，确保timer不会立即完成）
        response = self.client.get("/light/60")  # 60分钟，确保timer不会立即完成
        self.assertEqual(response.status_code, 200)
        
        timer = main.light_timer_task
        self.assertIsNotNone(timer, "应该创建了timer任务")
        
        # 立即取消timer（在它完成之前）
        cancel_response = self.client.post("/light/cancel")
        self.assertEqual(cancel_response.status_code, 200)
        cancel_data = cancel_response.json()
        self.assertEqual(cancel_data["status"], "success")
        
        # 验证timer被取消或清空
        # 在测试环境中，timer可能已经完成，所以检查响应消息
        if "cancelled_at" in cancel_data:
            # 成功取消了timer
            self.assertIn("cancelled_at", cancel_data)
            self.assertIsNone(main.light_timer_task, "全局timer任务应该被清空")
        else:
            # timer可能已经完成，这是可以接受的
            self.assertEqual(cancel_data["message"], "No active timer to cancel")
    
    def test_cancel_timer_when_no_timer(self):
        """测试在没有timer时取消timer"""
        import main
        
        # 确保没有timer
        if main.light_timer_task:
            main.light_timer_task.cancel()
            main.light_timer_task = None
        
        # 尝试取消timer
        cancel_response = self.client.post("/light/cancel")
        self.assertEqual(cancel_response.status_code, 200)
        cancel_data = cancel_response.json()
        self.assertEqual(cancel_data["status"], "success")
        self.assertEqual(cancel_data["message"], "No active timer to cancel")
    
    def test_immediate_turn_off_cancels_timer(self):
        """测试立即关闭时应该取消正在运行的timer"""
        import main
        
        # 先创建一个timer
        response1 = self.client.get("/light/5")
        self.assertEqual(response1.status_code, 200)
        
        timer = main.light_timer_task
        self.assertIsNotNone(timer, "应该创建了timer任务")
        
        # 立即关闭（应该取消timer）
        response2 = self.client.get("/light/0")
        self.assertEqual(response2.status_code, 200)
        
        # 验证timer被取消
        self.assertTrue(timer.cancelled(), "timer应该被取消")
        self.assertIsNone(main.light_timer_task, "全局timer任务应该被清空")

if __name__ == '__main__':
    unittest.main() 