#!/usr/bin/env python3
"""Build the README 1550 nm TE 1×4 MMI splitter demo layout."""

from __future__ import annotations

import argparse
from pathlib import Path

from gdsfactory_mcp.layout import build_1x4_mmi_network


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the 1550 nm TE 1×4 MMI network demo (GDS, JSON, PNG).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/mmi_1x4_1550_te"),
        help="Directory for JSON, GDS, and PNG outputs (default: build/mmi_1x4_1550_te)",
    )
    args = parser.parse_args()
    _, gds_path, png_path = build_1x4_mmi_network(args.output_dir)
    json_path = args.output_dir / "mmi_1x4_1550_te.json"
    print(f"JSON: {json_path.resolve()}")
    print(f"GDS: {gds_path.resolve()}")
    print(f"Preview: {png_path.resolve()}")


if __name__ == "__main__":
    main()
