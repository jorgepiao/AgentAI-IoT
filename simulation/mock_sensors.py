import argparse
import json
import math
import random
import signal
import sys
import time
from typing import Any

from config.mqtt_config import mqtt_config

SENSORS: list[dict[str, Any]] = [
    {
        "topic": "sala/sensor/temperatura",
        "range": (18.0, 30.0),
        "unit": "celsius",
        "decimals": 1,
        "behavior": {"type": "temperature", "base": 24.0, "amplitude": 3.0},
    },
    {
        "topic": "sala/sensor/humedad",
        "range": (30.0, 70.0),
        "unit": "percent",
        "decimals": 0,
        "behavior": {"type": "humidity", "base": 55, "amplitude": 10},
    },
    {
        "topic": "oficina/sensor/temperatura",
        "range": (18.0, 28.0),
        "unit": "celsius",
        "decimals": 1,
        "behavior": {"type": "temperature", "base": 22.0, "amplitude": 2.5},
    },
    {
        "topic": "oficina/sensor/luminosidad",
        "range": (50, 800),
        "unit": "lux",
        "decimals": 0,
        "behavior": {"type": "luminosity", "peak": 700},
    },
    {
        "topic": "dormitorio/sensor/temperatura",
        "range": (16.0, 26.0),
        "unit": "celsius",
        "decimals": 1,
        "behavior": {"type": "temperature", "base": 20.0, "amplitude": 2.0},
    },
    {
        "topic": "sala/sensor/movimiento",
        "range": (0, 1),
        "unit": "binary",
        "decimals": 0,
        "behavior": {"type": "binary_motion"},
    },
    {
        "topic": "sala/sensor/puerta",
        "range": (0, 1),
        "unit": "binary",
        "decimals": 0,
        "behavior": {"type": "binary_door"},
    },
]

_sim_state: dict[str, dict[str, Any]] = {}


def _build_temperature(sensor: dict[str, Any]) -> float:
    behavior = sensor["behavior"]
    base = behavior.get("base", 24.0)
    amp = behavior.get("amplitude", 3.0)
    hour = time.localtime().tm_hour
    temp = base + amp * math.sin(math.pi * (hour - 4) / 14)
    temp += random.gauss(0, 0.4)
    return round(temp, sensor["decimals"])


def _build_humidity(sensor: dict[str, Any]) -> float:
    behavior = sensor["behavior"]
    base = behavior.get("base", 55)
    amp = behavior.get("amplitude", 10)
    hour = time.localtime().tm_hour
    hum = base - 2 * math.sin(math.pi * (hour - 4) / 14) + random.gauss(0, 3)
    return round(max(20, min(90, hum)))


def _build_luminosity(sensor: dict[str, Any]) -> float:
    behavior = sensor["behavior"]
    peak = behavior.get("peak", 700)
    hour = time.localtime().tm_hour
    if hour < 6 or hour > 20:
        return 0
    rel = (hour - 6) / 7
    lux = peak * (1 - (rel - 1) ** 2)
    lux = max(0, lux + random.gauss(0, 40))
    return round(lux)


def _build_binary_motion(sensor: dict[str, Any]) -> int:
    topic = sensor["topic"]
    now = time.time()
    hour = time.localtime().tm_hour
    is_day = 7 <= hour <= 22

    state = _sim_state.get(topic)
    if state is None:
        state = {"mode": "idle", "next_change": now}
        _sim_state[topic] = state

    if state["mode"] == "detecting":
        state["counter"] -= 1
        if state["counter"] <= 0:
            state["mode"] = "idle"
            idle_range = (30, 120) if is_day else (60, 300)
            state["next_change"] = now + random.uniform(*idle_range)
        return 1

    if now >= state["next_change"]:
        state["mode"] = "detecting"
        state["counter"] = random.randint(3, 8)
        return 1
    return 0


def _build_binary_door(sensor: dict[str, Any]) -> int:
    topic = sensor["topic"]
    now = time.time()
    hour = time.localtime().tm_hour
    is_day = 7 <= hour <= 22

    state = _sim_state.get(topic)
    if state is None:
        state = {"mode": "closed", "next_change": now + random.uniform(30, 120)}
        _sim_state[topic] = state

    if state["mode"] == "open":
        if now >= state["next_change"]:
            state["mode"] = "closed"
            close_range = (60, 300) if is_day else (120, 600)
            state["next_change"] = now + random.uniform(*close_range)
        return 1

    if now >= state["next_change"]:
        state["mode"] = "open"
        state["next_change"] = now + random.uniform(5, 20)
        return 1
    return 0


_BUILDERS: dict[str, Any] = {
    "temperature": _build_temperature,
    "humidity": _build_humidity,
    "luminosity": _build_luminosity,
    "binary_motion": _build_binary_motion,
    "binary_door": _build_binary_door,
}


def build_payload(sensor: dict[str, Any]) -> dict[str, Any]:
    behavior = sensor.get("behavior")
    if behavior:
        builder = _BUILDERS.get(behavior.get("type"))
        if builder:
            value = builder(sensor)
            return {"value": value, "unit": sensor["unit"]}

    lo, hi = sensor["range"]
    if sensor["unit"] == "binary":
        value = random.choice([0, 1])
    else:
        value = round(random.uniform(lo, hi), sensor.get("decimals", 0))
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
