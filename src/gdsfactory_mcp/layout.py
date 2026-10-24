"""Small examples assembled through the reusable design core."""

from pathlib import Path

import gdsfactory as gf

from gdsfactory_mcp.backend import export_design, get_design_analysis_data
from gdsfactory_mcp.checks import run_design_checks
from gdsfactory_mcp.design import DesignService


def _export_checked_example(
    design: DesignService,
    output_dir: Path,
) -> tuple[gf.Component, Path, Path]:
    """Require a clean technology-neutral check before writing example files."""
    report = run_design_checks(design.spec)
    if not report["export_allowed"]:
        errors = [
            item["message"]
            for item in report["findings"]
            if item["severity"] == "error"
        ]
        raise ValueError(f"example design checks failed: {'; '.join(errors)}")
    design.save_json(output_dir / f"{design.spec.name}.json")
    return export_design(design.spec, output_dir)


def build_waveguide_taper(
    output_dir: Path,
    *,
    waveguide_length_um: float = 500.0,
    waveguide_width_um: float = 0.8,
    taper_length_um: float = 20.0,
    taper_output_width_um: float = 0.5,
) -> tuple[gf.Component, Path, Path]:
    """Build a straight waveguide connected to a taper.

    All geometric dimensions are expressed in micrometres.
    """
    design = DesignService("waveguide_taper")
    design.add_straight(
        "wg1",
        length_um=waveguide_length_um,
        width_um=waveguide_width_um,
    )
    design.add_taper(
        "taper1",
        length_um=taper_length_um,
        width1_um=waveguide_width_um,
        width2_um=taper_output_width_um,
    )
    design.connect("wg1", "o2", "taper1", "o1")
    return _export_checked_example(design, output_dir)


def build_bent_route(output_dir: Path) -> tuple[gf.Component, Path, Path]:
    """Build two fixed straight waveguides joined by a routed bent waveguide."""
    design = DesignService("bent_route")
    design.add_component("input", "straight", {"length": 20.0, "width": 0.5})
    design.add_component("output", "straight", {"length": 20.0, "width": 0.5})
    design.place_component("output", x_um=120, y_um=50)
    design.route(
        "input",
        "o2",
        "output",
        "o1",
        cross_section="strip",
        radius_um=10,
    )
    return _export_checked_example(design, output_dir)


def build_mmi_splitter(output_dir: Path) -> tuple[gf.Component, Path, Path]:
    """Build an MMI 1x2 circuit with one input and two routed outputs."""
    design = DesignService("mmi_splitter")
    design.add_component("input", "straight", {"length": 20.0, "width": 0.5})
    design.add_component("splitter", "mmi1x2", {})
    design.add_component("output_top", "straight", {"length": 20.0, "width": 0.5})
    design.add_component("output_bottom", "straight", {"length": 20.0, "width": 0.5})
    design.connect("input", "o2", "splitter", "o1")
    design.place_component("output_top", x_um=140, y_um=35)
    design.place_component("output_bottom", x_um=140, y_um=-35)
    design.route(
        "splitter", "o2", "output_top", "o1",
        cross_section="strip", radius_um=10,
    )
    design.route(
        "splitter", "o3", "output_bottom", "o1",
        cross_section="strip", radius_um=10,
    )
    return _export_checked_example(design, output_dir)


def build_1x4_mmi_network(
    output_dir: Path,
    *,
    stage_dx_um: float = 400.0,
    stage2_dy_um: float = 254.0,
    bend_radius_um: float = 100.0,
    gc_gap_um: float = 200.0,
    tree_x_um: float = 200.0,
) -> tuple[gf.Component, Path, Path]:
    """Build the README 1550 nm TE 1×4 MMI splitter demo.

    Uses a binary ``splitter_tree`` of three ``mmi1x2`` cells (strip cross-section,
    default 500 nm width), plus one input and four output elliptical grating
    couplers. Stage spacing matches the demo prompt: ``stage_dx_um`` between MMI
    levels and ``stage2_dy_um`` between the second-stage arms; output GC pitch is
    ``stage2_dy_um / 2`` (127 µm when using the defaults).
    """
    design = DesignService("mmi_1x4_1550_te")
    gc_parameters = {"polarization": "te", "wavelength": 1.55}
    design.add_component(
        "tree",
        "splitter_tree",
        {
            "noutputs": 4,
            "spacing_x": stage_dx_um,
            "spacing_y": stage2_dy_um,
        },
    )
    design.add_component("gc_in", "grating_coupler_elliptical", gc_parameters)
    for index in range(4):
        design.add_component(
            f"gc_out_{index}",
            "grating_coupler_elliptical",
            gc_parameters,
        )

    design.place_component("gc_in", x_um=0.0, y_um=0.0, rotation_deg=180)
    design.place_component("tree", x_um=tree_x_um, y_um=0.0)

    tree_ports = {
        port["name"]: port
        for port in get_design_analysis_data(design.spec)["ports_by_component"]["tree"]
    }
    output_ports = [f"o2_1_{index}" for index in range(1, 5)]
    for index, port_name in enumerate(output_ports):
        port_x, port_y = tree_ports[port_name]["center_um"]
        design.place_component(
            f"gc_out_{index}",
            x_um=port_x + gc_gap_um,
            y_um=port_y,
        )

    design.route(
        "gc_in",
        "o1",
        "tree",
        "o1_0_0",
        cross_section="strip",
        radius_um=bend_radius_um,
    )
    for index, port_name in enumerate(output_ports):
        design.route(
            "tree",
            port_name,
            f"gc_out_{index}",
            "o1",
            cross_section="strip",
            radius_um=bend_radius_um,
        )
    return _export_checked_example(design, output_dir)


def build_all_examples(
    output_root: Path,
) -> dict[str, tuple[gf.Component, Path, Path]]:
    """Generate all first-release examples in separate subdirectories."""
    builders = {
        "straight_taper": build_waveguide_taper,
        "bent_route": build_bent_route,
        "mmi_splitter": build_mmi_splitter,
    }
    return {
        name: builder(output_root / name)
        for name, builder in builders.items()
    }
