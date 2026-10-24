"""Optional layout export smoke test."""

from pathlib import Path

from gdsfactory_mcp.design import DesignService
from gdsfactory_mcp.layout import _export_checked_example


def test_export_straight_gds_to_tmp_path(tmp_path: Path) -> None:
    design = DesignService("smoke_straight")
    design.add_component("wg", "straight", {"length": 20.0, "width": 0.5})
    component, gds_path, png_path = _export_checked_example(design, tmp_path)

    assert component is not None
    assert gds_path.is_file()
    assert gds_path.suffix == ".gds"
    assert png_path.is_file()
    assert (tmp_path / "smoke_straight.json").is_file()
