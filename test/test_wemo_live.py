import os

import pytest

from services.wemo_service import WemoService


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_WEMO_LIVE_TESTS", "false").lower() != "true",
    reason="Set RUN_WEMO_LIVE_TESTS=true to run real Wemo device tests.",
)


def _service_with_live_config():
    service = WemoService()
    assert service.init_devices(), "Expected at least one configured Wemo device"
    return service


def test_live_wemo_status_for_configured_device():
    device_name = os.getenv("WEMO_LIVE_DEVICE", "coffee").lower()
    service = _service_with_live_config()

    result = service.get_all_status()

    assert device_name in result
    assert "error" not in result[device_name]
    assert result[device_name]["is_on"] in (0, 1, False, True)


def test_live_wemo_optional_toggle_round_trip():
    if os.getenv("WEMO_LIVE_TOGGLE", "false").lower() != "true":
        pytest.skip("Set WEMO_LIVE_TOGGLE=true to run a real toggle round trip.")

    device_name = os.getenv("WEMO_LIVE_DEVICE", "coffee").lower()
    service = _service_with_live_config()
    device = service.get_device(device_name)
    assert device is not None

    initial_state = bool(device.get_state())

    first = service.toggle(device_name)
    assert first["status"] == "success"
    assert bool(first["is_on"]) is not initial_state

    second = service.toggle(device_name)
    assert second["status"] == "success"
    assert bool(second["is_on"]) is initial_state
