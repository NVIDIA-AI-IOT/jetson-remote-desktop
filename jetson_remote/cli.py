"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .inspect import collect_report, render_human
from .edid import analyze_edid_file
from .planner import build_plan, render_plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jetson-remote",
        description="Safely inspect and plan remote desktop workflows for Jetson.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0-dev")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect_parser = commands.add_parser(
        "inspect", help="Collect a read-only platform and desktop report."
    )
    inspect_parser.add_argument(
        "--json", action="store_true", help="Write the report as JSON to stdout."
    )

    plan_parser = commands.add_parser(
        "plan", help="Recommend validation paths without changing the system."
    )
    plan_parser.add_argument(
        "--report",
        type=Path,
        help="Use a JSON report from 'inspect --json' instead of this host.",
    )
    edid_parser = commands.add_parser(
        "edid-inspect", help="Validate an EDID file without changing display state."
    )
    edid_parser.add_argument("path", type=Path)
    edid_parser.add_argument(
        "--json", action="store_true", help="Write the EDID report as JSON."
    )
    plan_parser.add_argument(
        "--json", action="store_true", help="Write the plan as JSON to stdout."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "inspect":
        report = collect_report()
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_human(report))
        return 0

    if args.command == "plan":
        if args.report:
            report = json.loads(args.report.read_text(encoding="utf-8"))
        else:
            report = collect_report()
        plan = build_plan(report)
        if args.json:
            print(json.dumps(plan, indent=2, sort_keys=True))
        else:
            print(render_plan(plan))
        return 0

    if args.command == "edid-inspect":
        report = analyze_edid_file(args.path)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            preferred = report.get("preferred_timing") or {}
            print(f"EDID: {report['path']}")
            print(f"Size: {report['size']} bytes")
            print(f"SHA-256: {report['sha256']}")
            print(f"Valid: {report['valid']}")
            print(f"Block checksums: {report['block_checksums_valid']}")
            if preferred:
                print(
                    "Preferred: "
                    f"{preferred['width']}x{preferred['height']}@{preferred['refresh_hz']}"
                )
            print(f"CTA 1080p60: {report['supports_cta_1080p60']}")
        return 0 if report["valid"] else 1

    return 2
