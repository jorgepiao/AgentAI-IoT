import asyncio
import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from config.settings import settings
from config.mqtt_config import mqtt_config

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self) -> None:
        self.client = mqtt.Client(
            client_id=mqtt_config.client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self.state_cache: dict[str, Any] = {}
        self._connected = False

        if mqtt_config.username and mqtt_config.password:
            self.client.username_pw_set(
                mqtt_config.username, mqtt_config.password
            )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: dict, reason_code: int, properties: Any = None
    ) -> None:
        if reason_code == 0:
            self._connected = True
            logger.info("Conectado al broker MQTT en %s:%s", mqtt_config.host, mqtt_config.port)
            topic = f"{settings.mqtt_topic_prefix}+/sensor/#"
            client.subscribe(topic)
            logger.info("Suscrito a: %s", topic)
        else:
            logger.error("Error de conexión MQTT (código %d)", reason_code)

    def _on_disconnect(
        self, client: mqtt.Client, userdata: Any, reason_code: int, properties: Any = None
    ) -> None:
        self._connected = False
        if reason_code != 0:
            logger.warning("Desconexión inesperada del broker (código %d)", reason_code)

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode())
            self.state_cache[msg.topic] = payload
            logger.debug("Caché actualizada [%s]: %s", msg.topic, payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Mensaje MQTT inválido en %s: %s", msg.topic, exc)

    async def connect(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self.client.connect,
            mqtt_config.host,
            mqtt_config.port,
            mqtt_config.keepalive,
        )
        self.client.loop_start()

    async def disconnect(self) -> None:
        self.client.loop_stop()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.client.disconnect)
        self._connected = False

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        full_topic = f"{settings.mqtt_topic_prefix}{topic}"
        data = json.dumps(payload, ensure_ascii=False)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.client.publish, full_topic, data
        )
        logger.info("Publicado en %s: %s", full_topic, data)

    def get_state(self, topic: str) -> dict[str, Any] | None:
        full_topic = f"{settings.mqtt_topic_prefix}{topic}"
        return self.state_cache.get(full_topic)

    @property
    def is_connected(self) -> bool:
        return self._connected


mqtt_client: MQTTClient | None = None


async def get_mqtt_client() -> MQTTClient:
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
        await mqtt_client.connect()
    return mqtt_client
