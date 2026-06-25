import argparse
import json
import random
import signal
import sys
import time
from typing import Any

from config.mqtt_config import mqtt_config

SENSORS: list[dict[str, Any]] = [
    {"topic": "sala/sensor/temperatura",  "range": (18.0, 30.0), "unit": "celsius", "decimals": 1},
    {"topic": "sala/sensor/humedad",      "range": (30.0, 70.0), "unit": "percent", "decimals": 0},
    {"topic": "oficina/sensor/temperatura", "range": (18.0, 28.0), "unit": "celsius", "decimals": 1},
    {"topic": "oficina/sensor/luminosidad", "range": (50, 800), "unit": "lux", "decimals": 0},
    {"topic": "dormitorio/sensor/temperatura", "range": (16.0, 26.0), "unit": "celsius", "decimals": 1},
    {"topic": "sala/sensor/movimiento", "range": (0, 1), "unit": "binary", "decimals": 0},
]


def build_payload(sensor: dict[str, Any]) -> dict[str, Any]:
    lo, hi = sensor["range"]
    if sensor["unit"] == "binary":
        value = random.choice([0, 1])
    else:
        value = round(random.uniform(lo, hi), sensor["decimals"])
    return {"value": value, "unit": sensor["unit"]}


def dry_run_loop(interval: float) -> None:
    print("=== MOCK SENSORS (DRY-RUN) ===")
    print(f"Publicando cada {interval}s. Ctrl+C para salir.\n")
    try:
        while True:
            for sensor in SENSORS:
                payload = build_payload(sensor)
                print(f"[sim/{sensor['topic']}] {json.dumps(payload)}")
            print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulación de sensores detenida.")


def mqtt_loop(interval: float) -> None:
    import paho.mqtt.client as mqtt

    client = mqtt.Client(
        client_id="mock_sensors",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    if mqtt_config.username:
        client.username_pw_set(mqtt_config.username, mqtt_config.password)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"Conectado al broker MQTT en {mqtt_config.host}:{mqtt_config.port}")
        else:
            print(f"Error de conexión MQTT (código {reason_code})")
            sys.exit(1)

    client.on_connect = on_connect

    try:
        client.connect(mqtt_config.host, mqtt_config.port, mqtt_config.keepalive)
        client.loop_start()
    except Exception as e:
        print(f"Error conectando al broker MQTT: {e}")
        sys.exit(1)

    print(f"=== MOCK SENSORS ===")
    print(f"Publicando cada {interval}s en '{mqtt_config.host}:{mqtt_config.port}'")
    print("Ctrl+C para salir.\n")

    try:
        while True:
            for sensor in SENSORS:
                topic = f"sim/{sensor['topic']}"
                payload = build_payload(sensor)
                client.publish(topic, json.dumps(payload))
                print(f"[{topic}] {json.dumps(payload)}")
            print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nDeteniendo simulación de sensores...")
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simula sensores IoT publicando telemetría en MQTT")
    parser.add_argument(
        "--interval", "-i", type=float, default=5.0,
        help="Intervalo entre publicaciones en segundos (default: 5)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Solo imprime en consola, sin conectar MQTT",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal.default_int_handler)

    if args.dry_run:
        dry_run_loop(args.interval)
    else:
        mqtt_loop(args.interval)


if __name__ == "__main__":
    main()
