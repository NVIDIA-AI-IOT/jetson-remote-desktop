# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import unittest

from jetson_remote.planner import build_plan


def report(platform_id: str, release: int, revision: str, uinput: bool = True):
    return {
        "platform": {
            "id": platform_id,
            "l4t": {"present": True, "release": release, "revision": revision},
        },
        "devices": {
            "uinput": {"present": uinput, "writable": uinput},
        },
    }


class PlannerTests(unittest.TestCase):
    def test_thor_r39_2_is_sdk_candidate(self):
        plan = build_plan(report("jetson-agx-thor", 39, "2.0"))
        self.assertTrue(plan["video_codec_sdk_13_1"]["official_candidate"])

    def test_thor_r38_4_is_not_sdk_candidate(self):
        plan = build_plan(report("jetson-agx-thor", 38, "4"))
        self.assertFalse(plan["video_codec_sdk_13_1"]["official_candidate"])

    def test_agx_orin_r39_2_is_not_sdk_candidate(self):
        plan = build_plan(report("jetson-agx-orin", 39, "2.0"))
        self.assertFalse(plan["video_codec_sdk_13_1"]["official_candidate"])

    def test_orin_nano_uses_software_path(self):
        plan = build_plan(report("jetson-orin-nano", 39, "2.0"))
        self.assertEqual(plan["encoder_paths"][0]["id"], "software-h264")

    def test_missing_uinput_is_a_blocker(self):
        plan = build_plan(report("jetson-agx-thor", 39, "2.0", uinput=False))
        self.assertTrue(any("uinput" in item for item in plan["blockers"]))


if __name__ == "__main__":
    unittest.main()

