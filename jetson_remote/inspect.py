"""Read-only host inspection.

Every probe in this module must remain non-privileged and side-effect free.
Failures are recorded as unavailable values instead of triggering remediation.
"""

from __future__ import annotations

import datetime as dt
import glob
import os
import platform
import re
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

from .edid import analyze_edid


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _run(argv: list[str]) -> dict[str, Any]:
    if not shutil.which(argv[0]):
        return {"available": False, "exit_code": None, "stdout": None}
    try:
        result = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"available": True, "exit_code": None, "error": str(error)}
    return {
        "available": True,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip() or None,
    }


def _os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    text = _read("/etc/os-release") or ""
    for line in text.splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _l4t_version(release_text: str | None) -> dict[str, Any]:
    if not release_text:
        return {"present": False, "release": None, "revision": None}
    match = re.search(r"R(\d+)\s*\(release\),\s*REVISION:\s*([0-9.]+)", release_text)
    return {
        "present": True,
        "release": int(match.group(1)) if match else None,
        "revision": match.group(2) if match else None,
        "raw": release_text.splitlines()[0],
    }


def _platform_id(model: str | None, compatible: str | None) -> str:
    identity = f"{model or ''} {compatible or ''}".lower()
    if "thor" in identity or "tegra264" in identity:
        return "jetson-agx-thor"
    if "orin nano" in identity:
        return "jetson-orin-nano"
    if "agx orin" in identity:
        return "jetson-agx-orin"
    if "orin nx" in identity:
        return "jetson-orin-nx"
    if "tegra234" in identity:
        return "jetson-orin-unknown"
    return "unknown"


def _device(path: str) -> dict[str, Any]:
    item = Path(path)
    try:
        stat = item.stat()
    except (FileNotFoundError, PermissionError, OSError):
        return {"present": False, "readable": False, "writable": False}
    return {
        "present": True,
        "readable": os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
        "mode": oct(stat.st_mode & 0o7777),
        "major": os.major(stat.st_rdev),
        "minor": os.minor(stat.st_rdev),
    }


def _drm_connectors() -> list[dict[str, Any]]:
    connectors: list[dict[str, Any]] = []
    for status_path in sorted(glob.glob("/sys/class/drm/card*-*/status")):
        connector_dir = Path(status_path).parent
        status = _read(status_path)
        item: dict[str, Any] = {
            "name": connector_dir.name,
            "status": status,
        }
        edid_path = connector_dir / "edid"
        try:
            data = edid_path.read_bytes()
        except (FileNotFoundError, PermissionError, OSError):
            data = b""
        item["edid"] = analyze_edid(data) if data else {"size": 0, "valid": False}
        connectors.append(item)
    return connectors


def collect_report() -> dict[str, Any]:
    model = _read("/proc/device-tree/model")
    compatible_raw = _read("/proc/device-tree/compatible")
    compatible = compatible_raw.replace("\x00", ",") if compatible_raw else None
    l4t = _l4t_version(_read("/etc/nv_tegra_release"))
    os_release = _os_release()
    commands = [
        "sunshine",
        "ffmpeg",
        "gst-launch-1.0",
        "nvidia-smi",
        "loginctl",
        "tailscale",
    ]
    session = {
        "display": os.environ.get("DISPLAY"),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE"),
        "xdg_runtime_dir": os.environ.get("XDG_RUNTIME_DIR"),
    }
    return {
        "schema_version": 1,
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "read_only": True,
        "host": {
            "hostname": socket.gethostname(),
            "architecture": platform.machine(),
            "kernel": platform.release(),
        },
        "platform": {
            "id": _platform_id(model, compatible),
            "model": model,
            "compatible": compatible,
            "l4t": l4t,
        },
        "os": {
            "id": os_release.get("ID"),
            "version_id": os_release.get("VERSION_ID"),
            "pretty_name": os_release.get("PRETTY_NAME"),
        },
        "session": session,
        "devices": {
            "uinput": _device("/dev/uinput"),
            "uhid": _device("/dev/uhid"),
            "dri_render128": _device("/dev/dri/renderD128"),
            "v4l2_nvenc": _device("/dev/v4l2-nvenc"),
        },
        "display_topology": {
            "drm_connectors": _drm_connectors(),
        },
        "commands": {name: shutil.which(name) for name in commands},
        "probes": {
            "hostname_addresses": _run(["hostname", "-I"]),
            "graphical_sessions": _run(["loginctl", "list-sessions", "--no-legend"]),
        },
    }


def render_human(report: dict[str, Any]) -> str:
    host = report["host"]
    target = report["platform"]
    l4t = target["l4t"]
    lines = [
        "Jetson Remote Desktop inspection (read-only)",
        f"Host:       {host['hostname']}",
        f"Model:      {target.get('model') or 'not detected'}",
        f"Platform:   {target['id']}",
        f"L4T:        R{l4t['release']}.{l4t['revision']}" if l4t["present"] else "L4T:        not detected",
        f"OS:         {report['os'].get('pretty_name') or 'unknown'}",
        f"Kernel:     {host['kernel']}",
        f"Arch:       {host['architecture']}",
        f"Session:    {report['session'].get('xdg_session_type') or 'not exported'}",
        "",
        "Devices:",
    ]
    for name, value in report["devices"].items():
        access = "rw" if value.get("readable") and value.get("writable") else "limited"
        lines.append(f"  {name:16} {'present' if value['present'] else 'absent':7} {access}")
    lines.extend(["", "DRM connectors:"])
    for connector in report["display_topology"]["drm_connectors"]:
        edid = connector["edid"]
        lines.append(
            f"  {connector['name']:20} {connector.get('status') or 'unknown':12} "
            f"EDID={edid.get('size', 0)} bytes valid={edid.get('valid', False)}"
        )
    lines.extend(["", "No system changes were made."])
    return "\n".join(lines)
