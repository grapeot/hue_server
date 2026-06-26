import pytest

from services.meross_service import MerossService


class DummyDevice:
    uuid = "device-uuid"
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


@pytest.mark.asyncio
async def test_toggle_door_uses_local_http_backend(monkeypatch):
    service = MerossService()
    service.device = DummyDevice(is_open=True)
    service._local_ip = "192.0.2.10"
    service._key = "test-key"

    calls = []

    def fake_local_request(namespace, method, payload):
        calls.append((namespace, method, payload))
        if method == "GET":
            return {"state": {"channel": 1, "open": 1}}
        return {"state": {"channel": 1, "open": 1, "execute": 1}}

    monkeypatch.setattr(service, "_local_request", fake_local_request)

    result = await service.toggle_door(1)

    assert result["status"] == "success"
    assert result["backend"] == "meross_local_http"
    assert result["target_open"] is False
    assert result["executed"] == 1
    assert calls == [
        ("Appliance.GarageDoor.State", "GET", {"state": {"channel": 1}}),
        (
            "Appliance.GarageDoor.State",
            "SET",
            {"state": {"channel": 1, "open": 0, "uuid": "device-uuid"}},
        ),
    ]
