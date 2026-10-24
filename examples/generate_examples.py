#!/usr/bin/env python3
"""Generate the three first-release example layouts (JSON, GDS, PNG)."""

from __future__ import annotations

import argparse
from pathlib import Path

from gdsfactory_mcp.layout import build_all_examples


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate straight_taper, bent_route, and mmi_splitter examples.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("example_outputs"),
        help="Root directory for example subfolders (default: example_outputs)",
    )
    args = parser.parse_args()
    results = build_all_examples(args.output_dir)
    for name, (_, gds_path, png_path) in results.items():
        print(f"{name}:")
        print(f"  GDS: {gds_path.resolve()}")
        print(f"  Preview: {png_path.resolve()}")


if __name__ == "__main__":
    main()
