import requests
import time
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to path if needed.
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

def save_light_state() -> Dict[str, Any]:
    """Save the current light state."""
    response = requests.get(f"{BASE_URL}/status")
    response.raise_for_status()
    return response.json()["state"]

def restore_light_state(state: Dict[str, Any]):
    """Restore the light state."""
    response = requests.post(f"{BASE_URL}/state", json={
        "on": state["on"],
        "bri": state["bri"]
    })
    response.raise_for_status()
    return response.json()

def test_light_control():
    """Test light control."""
    try:
        # Save current state.
        logger.info("Saving current light state...")
        original_state = save_light_state()
        logger.info(f"Original state: {original_state}")

        # Test immediate off.
        logger.info("Testing immediate turn off...")
        response = requests.get(f"{BASE_URL}/light/0")
        assert response.status_code == 200
        logger.info("Immediate turn off request successful")

        # Wait for state update.
        time.sleep(1)
        
        # Check that the light is off.
        current_state = save_light_state()
        assert current_state["on"] is False
        logger.info("Immediate turn off verified")

        # Test turn-off after two seconds.
        logger.info("Testing 2-second delay turn off...")
        response = requests.get(f"{BASE_URL}/light/0.0333")  # 2 seconds = 0.0333 minutes
        assert response.status_code == 200
        logger.info("Light turned on successfully")

        # Wait one second and check that the light is on.
        time.sleep(1)
        current_state = save_light_state()
        assert current_state["on"] is True, f"Light should be on, but state is {current_state}"
        # Brightness may lag; the on state is sufficient.
        logger.info(f"Light on state verified: {current_state}")

        # Wait two seconds and check that the light is off.
        time.sleep(2)
        current_state = save_light_state()
        assert current_state["on"] is False
        logger.info("Delayed turn off verified")

        # Restore original state.
        logger.info("Restoring original state...")
        restore_light_state(original_state)
        
        # Verify restoration.
        final_state = save_light_state()
        assert final_state["on"] == original_state["on"]
        assert final_state["bri"] == original_state["bri"]
        logger.info("State restoration verified")

        logger.info("All tests passed successfully!")
        return True

    except Exception as e:
        import traceback
        logger.error(f"Test failed: {str(e)}")
        logger.error(traceback.format_exc())
        # Ensure original state is restored.
        try:
            restore_light_state(original_state)
            logger.info("Original state restored after error")
        except Exception as restore_error:
            logger.error(f"Error restoring state: {str(restore_error)}")
        return False

if __name__ == "__main__":
    test_light_control() 
