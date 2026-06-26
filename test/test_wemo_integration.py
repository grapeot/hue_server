"""
Wemo integration tests.
Tests real Wemo device control.

Skipped by default because it requires real devices and a running server.
Manual run: python test/test_wemo_integration.py
"""

import unittest
import requests
import time
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path.
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables.
load_dotenv()

# Configure logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8000"))
BASE_URL = f"http://localhost:{PORT}"


class TestWemoIntegration(unittest.TestCase):
    """Wemo integration tests."""
    
    @classmethod
    def setUpClass(cls):
        """Check whether tests should run."""
        skip_tests = os.getenv("RUN_WEMO_TESTS", "false").lower() != "true"
        if skip_tests and __name__ != "__main__":
            # Skip by default unless explicitly enabled.
            raise unittest.SkipTest("Wemo integration tests skipped by default. Set RUN_WEMO_TESTS=true to run.")
    
    def setUp(self):
        """Set up one test."""
        self.device_name = "Bedroom Light"
        logger.info(f"Preparing test device: {self.device_name}")
    
    def test_bedroom_light_control(self):
        """Test Bedroom Light switch control."""
        try:
            # 1. Fetch current device state.
            logger.info("Fetching current device state...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200, "Should fetch device state")
            initial_state = response.json()
            logger.info(f"Initial state: {initial_state}")
            
            initial_on = initial_state.get("state") == "on"
            
            # 2. Turn device on.
            logger.info("Turning device on...")
            response = requests.post(f"{BASE_URL}/wemo/{self.device_name}/on")
            self.assertEqual(response.status_code, 200, "Should turn device on")
            result = response.json()
            logger.info(f"Turn-on result: {result}")
            
            # Wait for state update.
            time.sleep(1)
            
            # 3. Verify device is on.
            logger.info("Verifying device is on...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200)
            current_state = response.json()
            logger.info(f"State after turn-on: {current_state}")
            self.assertEqual(current_state.get("state"), "on", "Device should be on")
            
            # 4. Wait five seconds.
            logger.info("Waiting five seconds...")
            time.sleep(5)
            
            # 5. Turn device off.
            logger.info("Turning device off...")
            response = requests.post(f"{BASE_URL}/wemo/{self.device_name}/off")
            self.assertEqual(response.status_code, 200, "Should turn device off")
            result = response.json()
            logger.info(f"Turn-off result: {result}")
            
            # Wait for state update.
            time.sleep(1)
            
            # 6. Verify device is off.
            logger.info("Verifying device is off...")
            response = requests.get(f"{BASE_URL}/wemo/{self.device_name}/status")
            self.assertEqual(response.status_code, 200)
            final_state = response.json()
            logger.info(f"State after turn-off: {final_state}")
            self.assertEqual(final_state.get("state"), "off", "Device should be off")
            
            logger.info("Test complete. All steps succeeded.")
            
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server. Ensure the server is running.")
        except Exception as e:
            import traceback
            logger.error(f"Test failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise


if __name__ == "__main__":
    # Enable tests automatically when this file is run directly.
    os.environ["RUN_WEMO_TESTS"] = "true"
    logger.info("Manual run mode: enabling Wemo integration tests")
    
    unittest.main()
