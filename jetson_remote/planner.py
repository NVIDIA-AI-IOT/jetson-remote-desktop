"""Evidence-based, read-only workflow selection."""

from __future__ import annotations

from typing import Any


def _l4t_at_least(report: dict[str, Any], release: int, revision: float) -> bool:
    l4t = report["platform"]["l4t"]
    if not l4t.get("present") or l4t.get("release") is None:
        return False
    current_release = int(l4t["release"])
    try:
        current_revision = float(l4t.get("revision") or 0)
    except ValueError:
        current_revision = 0
    return (current_release, current_revision) >= (release, revision)


def build_plan(report: dict[str, Any]) -> dict[str, Any]:
    platform_id = report["platform"]["id"]
    is_thor = platform_id == "jetson-agx-thor"
    is_orin_nano = platform_id == "jetson-orin-nano"
    sdk_13_1 = is_thor and _l4t_at_least(report, 39, 2.0)

    encoder_paths: list[dict[str, str]] = []
    if sdk_13_1:
        encoder_paths.append(
            {
                "id": "video-codec-sdk-nvencode",
                "status": "official-candidate",
                "reason": "Jetson Thor and L4T R39.2+ satisfy SDK 13.1 requirements.",
            }
        )
    if is_thor:
        encoder_paths.append(
            {
                "id": "sunshine-ffmpeg-nvenc",
                "status": "probe-required",
                "reason": "Sunshine must prove capture and FFmpeg NVENC on this exact image.",
            }
        )
        encoder_paths.append(
            {
                "id": "jetson-v4l2-gstreamer",
                "status": "probe-required",
                "reason": "Keep the Jetson multimedia path as an independent control.",
            }
        )
    elif is_orin_nano:
        encoder_paths.append(
            {
                "id": "software-h264",
                "status": "primary",
                "reason": "Orin Nano has no NVENC hardware block.",
            }
        )
    elif platform_id.startswith("jetson-"):
        encoder_paths.extend(
            [
                {
                    "id": "jetson-v4l2-gstreamer",
                    "status": "primary-candidate",
                    "reason": "Use the Jetson multimedia API; SDK 13.1 does not list this SoC.",
                },
                {
                    "id": "software-h264",
                    "status": "fallback",
                    "reason": "Establish a portable baseline before integration work.",
                },
            ]
        )
    else:
        encoder_paths.append(
            {
                "id": "software-h264",
                "status": "safe-baseline",
                "reason": "Platform is not confidently identified.",
            }
        )

    blockers: list[str] = []
    uinput = report["devices"]["uinput"]
    if not uinput["present"]:
        blockers.append("/dev/uinput is absent; full keyboard/mouse control is not yet available.")
    elif not uinput["writable"]:
        blockers.append("/dev/uinput exists but is not writable by the current user.")

    return {
        "schema_version": 1,
        "read_only": True,
        "platform_id": platform_id,
        "video_codec_sdk_13_1": {
            "official_candidate": sdk_13_1,
            "reason": (
                "Jetson Thor with L4T R39.2 or newer."
                if sdk_13_1
                else "Requires both Jetson Thor and L4T R39.2 or newer."
            ),
        },
        "encoder_paths": encoder_paths,
        "blockers": blockers,
        "next_phase": "probe",
        "changes_proposed": [],
    }


def render_plan(plan: dict[str, Any]) -> str:
    lines = [
        "Jetson Remote Desktop plan (read-only)",
        f"Platform: {plan['platform_id']}",
        "Video Codec SDK 13.1: "
        + ("official candidate" if plan["video_codec_sdk_13_1"]["official_candidate"] else "not an official candidate"),
        "",
        "Encoder paths:",
    ]
    for path in plan["encoder_paths"]:
        lines.append(f"  - {path['id']} [{path['status']}]: {path['reason']}")
    if plan["blockers"]:
        lines.append("")
        lines.append("Blockers:")
        lines.extend(f"  - {item}" for item in plan["blockers"])
    lines.extend(["", "No system changes were made."])
    return "\n".join(lines)

