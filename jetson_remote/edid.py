# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Small, dependency-free EDID validation helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


EDID_HEADER = bytes.fromhex("00ffffffffffff00")


def _detailed_timing(block: bytes) -> dict[str, Any] | None:
    if len(block) != 18:
        return None
    pixel_clock = int.from_bytes(block[0:2], "little") * 10_000
    if pixel_clock == 0:
        return None
    h_active = block[2] | ((block[4] & 0xF0) << 4)
    h_blank = block[3] | ((block[4] & 0x0F) << 8)
    v_active = block[5] | ((block[7] & 0xF0) << 4)
    v_blank = block[6] | ((block[7] & 0x0F) << 8)
    total = (h_active + h_blank) * (v_active + v_blank)
    refresh = pixel_clock / total if total else None
    return {
        "width": h_active,
        "height": v_active,
        "refresh_hz": round(refresh, 3) if refresh else None,
        "pixel_clock_hz": pixel_clock,
        "interlaced": bool(block[17] & 0x80),
    }


def analyze_edid(data: bytes) -> dict[str, Any]:
    block_aligned = bool(data) and len(data) % 128 == 0
    blocks = [data[index : index + 128] for index in range(0, len(data), 128)]
    checksums = [sum(block) % 256 == 0 for block in blocks if len(block) == 128]
    extension_count = data[126] if len(data) >= 128 else None
    detailed_timings: list[dict[str, Any]] = []
    if len(data) >= 128:
        for offset in range(54, 126, 18):
            timing = _detailed_timing(data[offset : offset + 18])
            if timing:
                detailed_timings.append(timing)

    cta_vics: list[int] = []
    for block in blocks[1:]:
        if len(block) != 128 or block[0] != 0x02:
            continue
        end = block[2] if 4 <= block[2] <= 127 else 127
        offset = 4
        while offset < end:
            header = block[offset]
            tag = header >> 5
            length = header & 0x1F
            payload = block[offset + 1 : offset + 1 + length]
            if tag == 0x02:
                cta_vics.extend(value & 0x7F for value in payload)
            offset += length + 1

    preferred = detailed_timings[0] if detailed_timings else None
    expected_size = None if extension_count is None else 128 * (1 + extension_count)
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header_valid": data.startswith(EDID_HEADER),
        "block_aligned": block_aligned,
        "block_checksums_valid": checksums,
        "extension_count": extension_count,
        "extension_count_matches_size": expected_size == len(data),
        "digital": bool(len(data) >= 21 and data[20] & 0x80),
        "preferred_timing": preferred,
        "detailed_timings": detailed_timings,
        "cta_vics": sorted(set(cta_vics)),
        "supports_cta_1080p60": 16 in cta_vics,
        "valid": bool(
            data.startswith(EDID_HEADER)
            and block_aligned
            and checksums
            and all(checksums)
            and expected_size == len(data)
        ),
    }


def analyze_edid_file(path: Path) -> dict[str, Any]:
    report = analyze_edid(path.read_bytes())
    report["path"] = str(path)
    return report
