"""Mini EDR endpoint agent.

Periodically reports system stats and running processes to the Mini EDR
backend, and performs simple file-integrity monitoring on a configurable
list of paths.

IMPORTANT: only run this on systems you own or are explicitly authorized to
monitor.

Usage:
    python agent.py [--config config.yaml]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import socket
import time
from pathlib import Path

import psutil
import requests
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("mini-edr-agent")

STATE_FILE = Path(__file__).parent / "agent_state.json"


# ---------------------------------------------------------------------------
# Config / state helpers
# ---------------------------------------------------------------------------


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f) or {}

    config.setdefault("server_url", "http://localhost:8000")
    config.setdefault("intervals", {})
    config["intervals"].setdefault("heartbeat_seconds", 30)
    config["intervals"].setdefault("process_seconds", 60)
    config["intervals"].setdefault("file_integrity_seconds", 300)
    config.setdefault("file_integrity", {})
    config["file_integrity"].setdefault("paths", [])
    return config


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            log.warning("State file is corrupt, starting fresh")
    return {"agent_id": None, "file_hashes": {}}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------


def get_local_ip() -> str | None:
    """Best-effort local IP address (the one used to reach the internet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.release(),
        "ip_address": get_local_ip(),
    }


# ---------------------------------------------------------------------------
# Backend communication
# ---------------------------------------------------------------------------


def register(server_url: str, info: dict) -> str | None:
    try:
        resp = requests.post(f"{server_url}/api/agents/register", json=info, timeout=10)
        resp.raise_for_status()
        agent_id = resp.json()["id"]
        log.info("Registered with backend, agent_id=%s", agent_id)
        return agent_id
    except requests.RequestException as exc:
        log.error("Failed to register with backend: %s", exc)
        return None


def send_heartbeat(server_url: str, agent_id: str) -> None:
    payload = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "ip_address": get_local_ip(),
    }
    try:
        resp = requests.post(
            f"{server_url}/api/agents/{agent_id}/heartbeat", json=payload, timeout=10
        )
        resp.raise_for_status()
        log.info(
            "Heartbeat sent (cpu=%.1f%%, ram=%.1f%%)",
            payload["cpu_percent"],
            payload["ram_percent"],
        )
    except requests.RequestException as exc:
        log.warning("Failed to send heartbeat: %s", exc)


def send_processes(server_url: str, agent_id: str) -> None:
    processes = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        info = proc.info
        if info.get("name") is None:
            continue
        processes.append(
            {
                "pid": info["pid"],
                "name": info["name"],
                "username": info.get("username"),
                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_percent": round(info.get("memory_percent") or 0.0, 2),
            }
        )

    try:
        resp = requests.post(
            f"{server_url}/api/agents/{agent_id}/processes",
            json={"processes": processes},
            timeout=15,
        )
        resp.raise_for_status()
        log.info("Uploaded %d processes", len(processes))
    except requests.RequestException as exc:
        log.warning("Failed to upload processes: %s", exc)


def send_alert(server_url: str, agent_id: str, alert_type: str, severity: str, message: str) -> None:
    payload = {"alert_type": alert_type, "severity": severity, "message": message}
    try:
        resp = requests.post(
            f"{server_url}/api/agents/{agent_id}/alerts", json=payload, timeout=10
        )
        resp.raise_for_status()
        log.info("Alert sent: [%s] %s", severity, message)
    except requests.RequestException as exc:
        log.warning("Failed to send alert: %s", exc)


# ---------------------------------------------------------------------------
# File integrity monitoring
# ---------------------------------------------------------------------------


def hash_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError as exc:
        log.warning("Could not hash %s: %s", path, exc)
        return None


def check_file_integrity(server_url: str, agent_id: str, paths: list[str], state: dict) -> None:
    hashes = state.setdefault("file_hashes", {})

    for path in paths:
        new_hash = hash_file(path)
        if new_hash is None:
            continue

        old_hash = hashes.get(path)
        if old_hash is None:
            log.info("Baseline hash recorded for %s", path)
        elif old_hash != new_hash:
            send_alert(
                server_url,
                agent_id,
                alert_type="file_integrity",
                severity="high",
                message=f"File changed: {path}",
            )

        hashes[path] = new_hash

    save_state(state)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini EDR endpoint agent")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "config.yaml"),
        help="Path to config.yaml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    state = load_state()

    server_url = config["server_url"].rstrip("/")
    intervals = config["intervals"]
    fim_paths = config["file_integrity"]["paths"]

    if not state.get("agent_id"):
        info = get_system_info()
        agent_id = register(server_url, info)
        while agent_id is None:
            log.info("Retrying registration in 10s...")
            time.sleep(10)
            agent_id = register(server_url, info)
        state["agent_id"] = agent_id
        save_state(state)
    else:
        agent_id = state["agent_id"]
        log.info("Using existing agent_id=%s", agent_id)

    next_run = {
        "heartbeat": 0.0,
        "processes": 0.0,
        "file_integrity": 0.0,
    }

    log.info("Mini EDR agent started. Reporting to %s", server_url)

    while True:
        now = time.monotonic()

        if now >= next_run["heartbeat"]:
            send_heartbeat(server_url, agent_id)
            next_run["heartbeat"] = now + intervals["heartbeat_seconds"]

        if now >= next_run["processes"]:
            send_processes(server_url, agent_id)
            next_run["processes"] = now + intervals["process_seconds"]

        if fim_paths and now >= next_run["file_integrity"]:
            check_file_integrity(server_url, agent_id, fim_paths, state)
            next_run["file_integrity"] = now + intervals["file_integrity_seconds"]

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Agent stopped.")
