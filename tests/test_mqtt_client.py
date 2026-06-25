import pytest
from unittest.mock import patch

from src.core.mqtt_client import MQTTClient


class TestMQTTClient:
    def test_initial_state(self):
        client = MQTTClient()
        assert client.state_cache == {}
        assert client.is_connected is False

    def test_on_message_updates_cache(self):
        client = MQTTClient()

        class FakeMsg:
            topic = "sim/sala/sensor/temperatura"
            payload = b'{"value": 24.5}'

        client._on_message(None, None, FakeMsg())
        assert client.state_cache["sim/sala/sensor/temperatura"] == {"value": 24.5}

    def test_on_message_invalid_json_ignored(self, caplog):
        client = MQTTClient()

        class FakeMsg:
            topic = "sim/sala/sensor/ruido"
            payload = b"not-json"

        client._on_message(None, None, FakeMsg())
        assert client.state_cache == {}

    def test_get_state_with_prefix(self):
        client = MQTTClient()
        client.state_cache["sim/oficina/sensor/temperatura"] = {"value": 22.0}

        state = client.get_state("oficina/sensor/temperatura")
        assert state == {"value": 22.0}

    def test_get_state_nonexistent(self):
        client = MQTTClient()
        assert client.get_state("ruta/inexistente") is None

    def test_mqtt_topic_prefix_simulation(self):
        with patch("src.core.mqtt_client.settings") as mock_settings:
            mock_settings.mqtt_topic_prefix = "sim/"
            client = MQTTClient()
            client.state_cache["sim/sala/luz"] = {"state": "on"}
            assert client.get_state("sala/luz") == {"state": "on"}

    def test_disconnect_not_connected(self):
        client = MQTTClient()
        assert client.is_connected is False
