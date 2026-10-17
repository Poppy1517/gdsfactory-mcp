from pathlib import Path

from gdsfactory_mcp.layout import build_waveguide_taper


def main() -> None:
    """Generate the first example layout."""
    _, gds_path, png_path = build_waveguide_taper(Path("build"))
    print(f"GDS: {gds_path.resolve()}")
    print(f"Preview: {png_path.resolve()}")
