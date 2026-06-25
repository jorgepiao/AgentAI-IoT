import argparse
import json
import signal
import sys
import time
from typing import Any

from config.mqtt_config import mqtt_config
from src.core.guardrails import DEVICE_REGISTRY


def describe_command(topic: str, payload: dict[str, Any]) -> str:
    parts = topic.strip("/").split("/")
    room = parts[1] if len(parts) > 1 else "?"
    device_id = parts[3] if len(parts) > 3 else "?"
    action = payload.get("action", payload.get("state", "?"))

    full_device_id = f"{room}.{device_id}" if room != "?" and device_id != "?" else device_id
    device_info = DEVICE_REGISTRY.get(full_device_id, {})
    label = device_info.get("label", device_id)

    if action == "on":
        return f"🔦 {label} ({room}) → ENCENDIDO"
    if action == "off":
        return f"🔦 {label} ({room}) → APAGADO"
    if action == "set_brightness":
        brightness = payload.get("params", {}).get("brightness", "?")
        return f"💡 {label} ({room}) → BRILLO {brightness}%"
    if action == "set_temperature":
        temp = payload.get("params", {}).get("temperature", "?")
        return f"🌡️ {label} ({room}) → TEMPERATURA {temp}°C"
    if action == "set_mode":
        mode = payload.get("params", {}).get("mode", "?")
        return f"❄️ {label} ({room}) → MODO {mode.upper()}"

    device_type = device_info.get("type", "")
    if device_type == "cover":
        if action == "open":
            return f"🪟 {label} ({room}) → SUBIR"
        if action == "close":
            return f"🪟 {label} ({room}) → BAJAR"
        if action == "set_position":
            position = payload.get("params", {}).get("position", "?")
            return f"🪟 {label} ({room}) → POSICIÓN {position}%"
    if device_type == "fan":
        if action == "on":
            return f"🌀 {label} ({room}) → ENCENDIDO"
        if action == "off":
            return f"🌀 {label} ({room}) → APAGADO"
        if action == "set_speed":
            speed = payload.get("params", {}).get("speed", "?")
            return f"🌀 {label} ({room}) → VELOCIDAD {speed}%"

    if device_type in ("switch", "appliance"):
        if action == "on":
            return f"🔌 {label} ({room}) → ENCENDIDO"
        if action == "off":
            return f"🔌 {label} ({room}) → APAGADO"

    return f"⚙️ {label} ({room}) → {action} {payload.get('params', {})}"


def build_status_response(topic: str, payload: dict[str, Any]) -> dict[str, Any]:
    parts = topic.strip("/").split("/")
    room = parts[1] if len(parts) > 1 else "?"
    device_id = parts[3] if len(parts) > 3 else "unknown"
    full_device_id = f"{room}.{device_id}" if room != "?" and device_id != "unknown" else device_id
    action = payload.get("action", payload.get("state", ""))
    params = payload.get("params", {})
    device_info = DEVICE_REGISTRY.get(full_device_id, {})

    off_actions = {"off", "close", "turn_off"}
    status: dict[str, Any] = {"state": "off" if action in off_actions else "on"}

    device_type = device_info.get("type", "")

    if device_type == "light":
        if action == "set_brightness":
            status["brightness"] = params.get("brightness", 100)
        elif status["state"] == "on":
            status["brightness"] = 100

    if device_type == "climate":
        if action == "set_temperature":
            status["temperature"] = params.get("temperature", 22)
            status["mode"] = "cool"
        elif action == "set_mode":
            status["mode"] = params.get("mode", "auto")
            status["temperature"] = 22
        elif status["state"] == "on":
            status["temperature"] = 22
            status["mode"] = "cool"

    if device_type == "cover":
        if action == "set_position":
            status["position"] = params.get("position", 100)
        elif action == "open":
            status["position"] = 100
        elif action == "close":
            status["position"] = 0

    if device_type == "fan":
        if action == "set_speed":
            status["speed"] = params.get("speed", 100)
        elif status["state"] == "on":
            status["speed"] = 100

    return status


def on_message(client, userdata, msg) -> None:
    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"⚠️ Mensaje inválido en {msg.topic}: {e}")
        return

    print(describe_command(msg.topic, payload))

    status_topic = msg.topic.replace("/set", "/status")
    status = build_status_response(msg.topic, payload)
    client.publish(status_topic, json.dumps(status))
    print(f"   ↳ Estado publicado en [{status_topic}]: {json.dumps(status)}")


def dry_run(topic_filter: str) -> None:
    print("=== MOCK ACTUADORES (DRY-RUN) ===")
    print(f"Modo seco — suscripción planeada: {topic_filter}")
    print("Los comandos se mostrarían aquí. Ctrl+C para salir.\n")
    print("Ejecuta sin --dry-run para conectar con MQTT:\n")
    print(f"  python -m simulation.mock_actuadores\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def mqtt_listen(topic_filter: str) -> None:
    import paho.mqtt.client as mqtt

    client = mqtt.Client(
        client_id="mock_actuadores",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    if mqtt_config.username:
        client.username_pw_set(mqtt_config.username, mqtt_config.password)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"Conectado al broker MQTT en {mqtt_config.host}:{mqtt_config.port}")
            c.subscribe(topic_filter)
            print(f"Escuchando comandos en: {topic_filter}")
            print("Esperando comandos... (Ctrl+C para salir)\n")
        else:
            print(f"Error de conexión MQTT (código {reason_code})")
            sys.exit(1)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(mqtt_config.host, mqtt_config.port, mqtt_config.keepalive)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo simulador de actuadores...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simula actuadores IoT escuchando comandos MQTT y emulando respuestas"
    )
    parser.add_argument(
        "--topic", "-t", type=str, default="sim/+/actuator/+/set",
        help="Filtro de tópico MQTT a escuchar (default: sim/+/actuator/+/set)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Solo muestra qué haría, sin conectar MQTT",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal.default_int_handler)

    if args.dry_run:
        dry_run(args.topic)
    else:
        mqtt_listen(args.topic)


if __name__ == "__main__":
    main()
