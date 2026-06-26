import pytest

from services.meross_service import MerossService


class DummyDevice:
    uuid = "device-uuid"
    name = "Garage Controller"
    channels = [{}, {}, {}]

    def __init__(self, is_open=False):
        self._is_open = is_open

    def get_is_open(self, door_index):
        return self._is_open


def test_build_local_message_has_signed_header(monkeypatch):
    service = MerossService()
    service.device = DummyDevice()
    service._local_ip = "192.0.2.10"
    service._key = "test-key"

    monkeypatch.setattr("services.meross_service.time.time", lambda: 1234567890)
    monkeypatch.setattr("services.meross_service.secrets.token_hex", lambda n: "abc123")

    message = service._build_local_message(
        "Appliance.GarageDoor.State",
        "SET",
        {"state": {"channel": 1, "open": 0}},
    )

    header = message["header"]
    assert header["messageId"] == "abc123"
    assert header["namespace"] == "Appliance.GarageDoor.State"
    assert header["method"] == "SET"
    assert header["from"] == "http://192.0.2.10/config"
    assert header["uuid"] == "device-uuid"
    assert header["sign"] == "f94a53353b58257ae7b1aa38561bf2c6"


def test_get_current_open_state_prefers_local_payload():
    service = MerossService()
    service.device = DummyDevice(is_open=False)

    assert service._get_current_open_state(1, {"open": 1}) is True
    assert service._get_current_open_state(1, {"open": 0}) is False


def test_get_current_open_state_falls_back_to_sdk_state():
    service = MerossService()
    service.device = DummyDevice(is_open=True)

    assert service._get_current_open_state(1, {}) is True


def test_select_garage_device_by_uuid(monkeypatch):
    service = MerossService()
    devices = [DummyDevice(), DummyDevice()]
    devices[0].uuid = "wrong"
    devices[1].uuid = "expected"

    monkeypatch.setenv("MEROSS_GARAGE_UUID", "expected")

    assert service._select_garage_device(devices) is devices[1]


def test_select_garage_device_requires_selector_for_multiple_devices(monkeypatch):
    service = MerossService()
    monkeypatch.delenv("MEROSS_GARAGE_UUID", raising=False)
    monkeypatch.delenv("MEROSS_GARAGE_NAME", raising=False)

    assert service._select_garage_device([DummyDevice(), DummyDevice()]) is None


@pytest.mark.asyncio
async def test_toggle_door_uses_local_http_backend(monkeypatch):
    service = MerossService()
    service.device = DummyDevice(is_open=True)
    service._local_ip = "192.0.2.10"
    service._key = "test-key"
    service._verify_timeout_seconds = 0.1
    service._verify_poll_interval_seconds = 0.01

    calls = []
    get_calls = 0

    def fake_local_request(namespace, method, payload):
        nonlocal get_calls
        calls.append((namespace, method, payload))
        if method == "GET":
            get_calls += 1
            return {"state": {"channel": 1, "open": 1 if get_calls == 1 else 0}}
        return {"state": {"channel": 1, "open": 1, "execute": 1}}

    monkeypatch.setattr(service, "_local_request", fake_local_request)

    result = await service.toggle_door(1)

    assert result["status"] == "success"
    assert result["backend"] == "meross_local_http"
    assert result["target_open"] is False
    assert result["verified"] is True
    assert result["final_state"]["open"] == 0
    assert result["executed"] == 1
    assert calls[:2] == [
        ("Appliance.GarageDoor.State", "GET", {"state": {"channel": 1}}),
        (
            "Appliance.GarageDoor.State",
            "SET",
            {"state": {"channel": 1, "open": 0, "uuid": "device-uuid"}},
        ),
    ]


@pytest.mark.asyncio
async def test_toggle_door_reports_unverified_when_state_does_not_change(monkeypatch):
    service = MerossService()
    service.device = DummyDevice(is_open=True)
    service._local_ip = "192.0.2.10"
    service._key = "test-key"
    service._verify_timeout_seconds = 0.01
    service._verify_poll_interval_seconds = 0.01

    def fake_local_request(namespace, method, payload):
        if method == "GET":
            return {"state": {"channel": 1, "open": 1}}
        return {"state": {"channel": 1, "open": 1, "execute": 1}}

    monkeypatch.setattr(service, "_local_request", fake_local_request)

    result = await service.toggle_door(1)

    assert result["status"] == "triggered_unverified"
    assert result["verified"] is False
    assert result["target_open"] is False
    assert "not verified" in result["message"]
