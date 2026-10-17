"""Convert validated design descriptions into gdsfactory geometry."""

from pathlib import Path
from functools import partial
from math import cos, hypot, radians, sin
from typing import Any

import matplotlib

matplotlib.use("Agg")

import gdsfactory as gf
from gdsfactory.components.waveguides.crossing_waveguide import crossing_arm
from kfactory import kdb
from matplotlib import pyplot as plt
from shapely.geometry import LineString

from gdsfactory_mcp.models import (
    DesignSpec,
    GenericComponentSpec,
    StraightSpec,
    TaperSpec,
)
from gdsfactory_mcp.technology import activate_technology, get_cross_section_profile

_built_top_cells: dict[str, gf.Component] = {}


def _resolve_registered_parameters(parameters: dict[str, object]) -> dict[str, object]:
    """Resolve validated JSON references into gdsfactory registry names."""
    resolved = {}
    for name, value in parameters.items():
        if isinstance(value, dict) and value.get("kind") == "registered_reference":
            resolved[name] = value["name"]
        else:
            resolved[name] = value
    return resolved


def _build_component_with_references(
    design: DesignSpec,
    *,
    apply_connections: bool = True,
    route_records: list[dict[str, Any]] | None = None,
) -> tuple[gf.Component, dict[str, Any]]:
    """Build a design and retain its placed component references."""
    activate_technology()
    previous_top = _built_top_cells.pop(design.name, None)
    if previous_top is not None:
        gf.kcl.delete_cell(previous_top)
    top = gf.Component(design.name)
    _built_top_cells[design.name] = top
    references = {}

    for component in design.components:
        if isinstance(component, StraightSpec):
            cell = gf.components.straight(
                length=component.length_um,
                width=component.width_um,
            )
        elif isinstance(component, TaperSpec):
            cell = gf.components.taper(
                length=component.length_um,
                width1=component.width1_um,
                width2=component.width2_um,
            )
        elif isinstance(component, GenericComponentSpec):
            parameters = _resolve_registered_parameters(component.parameters)
            if component.type_name == "straight":
                cell = gf.components.straight(**parameters)
            elif component.type_name == "taper":
                cell = gf.components.taper(**parameters)
            elif component.type_name == "bend_euler":
                cell = gf.components.bend_euler(**parameters)
            elif component.type_name == "bend_s":
                size = (parameters.pop("size_x"), parameters.pop("size_y"))
                cell = gf.components.bend_s(size=size, **parameters)
            elif component.type_name == "crossing":
                arm = partial(
                    crossing_arm,
                    r1=parameters.pop("r1"),
                    r2=parameters.pop("r2"),
                    w=parameters.pop("arm_width"),
                    L=parameters.pop("arm_length"),
                    **parameters,
                )
                cell = gf.components.crossing(arm=arm)
            elif component.type_name == "taper_adiabatic":
                cell = gf.components.taper_adiabatic(
                    length=0,
                    cross_section="strip",
                    **parameters,
                )
            elif component.type_name == "mmi1x2":
                cell = gf.components.mmi1x2(**parameters)
            elif component.type_name == "mmi2x2":
                cell = gf.components.mmi2x2(**parameters)
            elif component.type_name == "coupler":
                cell = gf.components.coupler(**parameters)
            elif component.type_name == "coupler_straight":
                cell = gf.components.coupler_straight(**parameters)
            elif component.type_name == "coupler_ring":
                cell = gf.components.coupler_ring(**parameters)
            elif component.type_name == "ring_single":
                cell = gf.components.ring_single(**parameters)
            elif component.type_name == "ring_double":
                cell = gf.components.ring_double(**parameters)
            elif component.type_name == "coupled_ring_chain":
                radius = parameters.pop("radius")
                width = parameters.pop("waveguide_width")
                gaps = tuple(
                    parameters.pop(name)
                    for name in (
                        "gap_input", "gap_12", "gap_23", "gap_34", "gap_output",
                    )
                )
                length_x = parameters.pop("coupling_length")
                length_y = parameters.pop("vertical_straight_length")
                include_electrodes = parameters.pop("include_electrodes")
                pad_width = parameters.pop("pad_width")
                pad_height = parameters.pop("pad_height")
                metal_width = parameters.pop("metal_width")
                rib = partial(gf.cross_section.rib, width=width)
                core = gf.components.ring_crow(
                    gaps=gaps,
                    radius=(radius,) * 4,
                    ring_cross_sections=(rib,) * 4,
                    length_x=length_x,
                    lengths_y=(length_y,) * 4,
                    input_straight_cross_section=rib,
                    output_straight_cross_section=rib,
                    cross_section=rib,
                )
                cell = gf.Component()
                core_ref = cell << core
                core_ref.drotate(-90)

                layer = gf.get_layer("WG")
                external_ports = {
                    "input": gf.Port(name="input", width=width, layer=layer, center=(-25, 10), orientation=180),
                    "through": gf.Port(name="through", width=width, layer=layer, center=(110, -32), orientation=0),
                    "drop": gf.Port(name="drop", width=width, layer=layer, center=(110, -10.01), orientation=0),
                    "add": gf.Port(name="add", width=width, layer=layer, center=(110, 10), orientation=0),
                }
                for port_name, core_port in (("input", "o1"), ("drop", "o4"), ("add", "o3")):
                    gf.routing.route_single(
                        cell, core_ref.ports[core_port], external_ports[port_name],
                        cross_section=rib, radius=7, on_collision="warning",
                    )
                gf.routing.route_single(
                    cell, core_ref.ports["o2"], external_ports["through"],
                    cross_section=rib, radius=7,
                    waypoints=[(0, -32), (100, -32)],
                    on_collision="warning",
                )
                for port_name, port in external_ports.items():
                    cell.add_port(port_name, port=port)

                if include_electrodes:
                    centers = (0.0, 28.06, 56.11, 84.17)
                    for center_x in centers:
                        metal_ring = cell << gf.components.ring(
                            radius=radius - 2.0, width=metal_width, layer="M1",
                        )
                        metal_ring.dmove((center_x, 0))
                    pad_y = -78.0
                    for center_x in (8.0, 42.0, 76.0):
                        pad = cell << gf.components.rectangle(
                            size=(pad_width, pad_height), layer="MTOP",
                            centered=True,
                        )
                        pad.dmove((center_x, pad_y))
                    signal = cell << gf.components.rectangle(
                        size=(metal_width, 70), layer="M1", centered=True,
                    )
                    signal.dmove((42.0, -38.0))
                    for x0, x1 in ((8.0, 0.0), (76.0, 84.17)):
                        trace = cell << gf.components.rectangle(
                            size=(metal_width, 58), layer="M1", centered=True,
                        )
                        trace.drotate(-25 if x0 < x1 else 25)
                        trace.dmove(((x0 + x1) / 2, -45.0))
            elif component.type_name == "disk":
                cell = gf.components.disk(**parameters)
            elif component.type_name == "grating_coupler_elliptical":
                cell = gf.components.grating_coupler_elliptical(**parameters)
            elif component.type_name == "grating_coupler_rectangular":
                cell = gf.components.grating_coupler_rectangular(**parameters)
            elif component.type_name == "edge_coupler_silicon":
                cell = gf.components.edge_coupler_silicon(**parameters)
            elif component.type_name == "edge_coupler_array":
                include_text = parameters.pop("include_text")
                edge_coupler = partial(
                    gf.components.edge_coupler_silicon,
                    length=parameters.pop("length"),
                    width1=parameters.pop("width1"),
                    width2=parameters.pop("width2"),
                    cross_section=parameters.pop("cross_section", "strip"),
                )
                cell = gf.components.edge_coupler_array(
                    edge_coupler=edge_coupler,
                    text="text_rectangular" if include_text else None,
                    **parameters,
                )
            elif component.type_name == "spiral":
                cell = gf.components.spiral(**parameters)
            elif component.type_name == "spiral_racetrack_fixed_length":
                cell = gf.components.spiral_racetrack_fixed_length(**parameters)
            elif component.type_name == "delay_snake_sbend":
                cell = gf.components.delay_snake_sbend(**parameters)
            elif component.type_name == "mzi":
                cell = gf.components.mzi(**parameters)
            elif component.type_name == "mzi2x2_2x2_phase_shifter":
                cell = gf.components.mzi2x2_2x2_phase_shifter(**parameters)
            elif component.type_name == "straight_heater_metal":
                cell = gf.components.straight_heater_metal(**parameters)
            elif component.type_name == "splitter_tree":
                spacing = (
                    parameters.pop("spacing_x"),
                    parameters.pop("spacing_y"),
                )
                cell = gf.components.splitter_tree(spacing=spacing, **parameters)
            elif component.type_name == "dbr":
                cell = gf.components.dbr(**parameters)
            elif component.type_name == "loop_mirror":
                cross_section = parameters.pop("cross_section", "strip")
                splitter = partial(
                    gf.components.mmi1x2,
                    cross_section=cross_section,
                    **parameters,
                )
                cell = gf.components.loop_mirror(
                    component=splitter,
                    bend90="bend_euler",
                    cross_section=cross_section,
                )
            else:  # pragma: no cover - validated safe adapters prevent this
                raise TypeError(
                    f"unsupported generic component: {component.type_name}"
                )
        else:  # pragma: no cover - the validated model prevents this branch
            raise TypeError(f"unsupported component: {component}")
        reference = top << cell
        if component.placement.mirror_x:
            reference.dmirror_y(0)
        if component.placement.rotation_deg:
            reference.drotate(component.placement.rotation_deg, center=(0, 0))
        if component.placement.x_um or component.placement.y_um:
            reference.dmove((component.placement.x_um, component.placement.y_um))
        references[component.name] = reference

    connected_ports: set[tuple[str, str]] = set()
    if apply_connections:
        for connection in (
            item for item in design.connections if item.connection_type == "direct"
        ):
            source = references[connection.source_component]
            target = references[connection.target_component]
            target.connect(connection.target_port, source.ports[connection.source_port])
            connected_ports.add((connection.source_component, connection.source_port))
            connected_ports.add((connection.target_component, connection.target_port))

        for connection in (
            item for item in design.connections if item.connection_type == "route"
        ):
            source = references[connection.source_component]
            target = references[connection.target_component]
            route = gf.routing.route_single(
                top,
                source.ports[connection.source_port],
                target.ports[connection.target_port],
                cross_section=connection.cross_section.name,
                radius=connection.radius_um,
                waypoints=(
                    list(connection.waypoints_um)
                    if connection.waypoints_um
                    else None
                ),
                on_placer_error="error",
            )
            if route_records is not None:
                layer_info = source.ports[connection.source_port].layer_info
                route_records.append({
                    "source": (
                        f"{connection.source_component}."
                        f"{connection.source_port}"
                    ),
                    "target": (
                        f"{connection.target_component}."
                        f"{connection.target_port}"
                    ),
                    "source_center_um": [
                        float(value)
                        for value in source.ports[connection.source_port].dcenter
                    ],
                    "target_center_um": [
                        float(value)
                        for value in target.ports[connection.target_port].dcenter
                    ],
                    "layer": {
                        "layer": int(layer_info.layer),
                        "datatype": int(layer_info.datatype),
                    },
                    "backbone_um": [
                        [float(point.x) * gf.kcl.dbu, float(point.y) * gf.kcl.dbu]
                        for point in route.backbone
                    ],
                })
            connected_ports.add((connection.source_component, connection.source_port))
            connected_ports.add((connection.target_component, connection.target_port))

    for component in design.components:
        reference = references[component.name]
        for port in reference.ports:
            if (component.name, port.name) not in connected_ports:
                top.add_port(f"{component.name}__{port.name}", port=port)

    return top, references


def build_component(design: DesignSpec) -> gf.Component:
    """Build a gdsfactory component from a validated design description."""
    top, _ = _build_component_with_references(design)
    return top


def get_component_ports_data(
    design: DesignSpec,
    component_name: str,
    *,
    apply_connections: bool = True,
) -> list[dict[str, Any]]:
    """Return JSON-compatible, placed port data for one named component."""
    if component_name not in {component.name for component in design.components}:
        raise ValueError(f"component not found: {component_name}")

    _, references = _build_component_with_references(
        design,
        apply_connections=apply_connections,
    )
    reference = references[component_name]
    connected_ports = {
        (connection.source_component, connection.source_port)
        for connection in design.connections
    } | {
        (connection.target_component, connection.target_port)
        for connection in design.connections
    }

    ports = []
    for port in reference.ports:
        layer_info = port.layer_info
        ports.append({
            "name": port.name,
            "center_um": [float(coordinate) for coordinate in port.dcenter],
            "orientation_deg": float(port.orientation),
            "width_um": float(port.dwidth),
            "layer": {
                "name": layer_info.name or None,
                "layer": int(layer_info.layer),
                "datatype": int(layer_info.datatype),
            },
            "port_type": port.port_type,
            "is_connected": (component_name, port.name) in connected_ports,
        })
    return ports


def get_route_cross_section_data(name: str) -> dict[str, float | None]:
    """Return nominal width and minimum radius for a registered cross-section."""
    profile = get_cross_section_profile(name)
    return {
        "width_um": profile["default_width_um"],
        "default_radius_um": profile["default_radius_um"],
        "min_radius_um": profile["minimum_radius_um"],
    }


def get_component_placement_data(
    design: DesignSpec,
    component_name: str,
) -> dict[str, float | bool]:
    """Return the final transform after direct connections have been applied."""
    if component_name not in {component.name for component in design.components}:
        raise ValueError(f"component not found: {component_name}")
    _, references = _build_component_with_references(design)
    transform = references[component_name].dcplx_trans
    return {
        "x_um": float(transform.disp.x),
        "y_um": float(transform.disp.y),
        "rotation_deg": float(transform.angle),
        "mirror_x": bool(transform.mirror),
        "is_explicit": True,
    }


def get_design_analysis_data(design: DesignSpec) -> dict[str, Any]:
    """Return placed ports and exact same-layer overlaps for design checks."""
    route_records: list[dict[str, Any]] = []
    component, references = _build_component_with_references(
        design,
        route_records=route_records,
    )
    ports_by_component: dict[str, list[dict[str, Any]]] = {}
    for component_name, reference in references.items():
        ports_by_component[component_name] = [
            {
                "name": port.name,
                "center_um": [float(value) for value in port.dcenter],
                "orientation_deg": float(port.orientation),
                "width_um": float(port.dwidth),
                "port_type": port.port_type,
            }
            for port in reference.ports
        ]

    overlaps: list[dict[str, Any]] = []
    component_names = list(references)
    for first_index, first_name in enumerate(component_names):
        first = references[first_name]
        for second_name in component_names[first_index + 1:]:
            second = references[second_name]
            if not first.dbbox().overlaps(second.dbbox()):
                continue
            for layer, datatype in sorted(component.layers):
                layer_index = gf.kcl.layer(layer, datatype)
                first_region = kdb.Region(first.cell.begin_shapes_rec(layer_index))
                second_region = kdb.Region(second.cell.begin_shapes_rec(layer_index))
                if first_region.is_empty() or second_region.is_empty():
                    continue
                first_region.transform(first.cplx_trans)
                second_region.transform(second.cplx_trans)
                overlap = first_region & second_region
                area_um2 = float(overlap.area()) * gf.kcl.dbu**2
                if area_um2 > 0:
                    overlaps.append({
                        "component_a": first_name,
                        "component_b": second_name,
                        "layer": {"layer": int(layer), "datatype": int(datatype)},
                        "area_um2": area_um2,
                    })
    route_crossings: list[dict[str, Any]] = []
    route_endpoint_gaps: list[dict[str, Any]] = []
    endpoint_tolerance_um = max(gf.kcl.dbu, 1e-6)
    for route in route_records:
        backbone = route["backbone_um"]
        if not backbone:
            route_endpoint_gaps.append({
                "source": route["source"],
                "target": route["target"],
                "source_gap_um": None,
                "target_gap_um": None,
                "reason": "empty_route_backbone",
            })
            continue
        source_gap = hypot(
            backbone[0][0] - route["source_center_um"][0],
            backbone[0][1] - route["source_center_um"][1],
        )
        target_gap = hypot(
            backbone[-1][0] - route["target_center_um"][0],
            backbone[-1][1] - route["target_center_um"][1],
        )
        if source_gap > endpoint_tolerance_um or target_gap > endpoint_tolerance_um:
            route_endpoint_gaps.append({
                "source": route["source"],
                "target": route["target"],
                "source_gap_um": float(source_gap),
                "target_gap_um": float(target_gap),
                "reason": "route_backbone_does_not_reach_ports",
            })
    for first_index, first in enumerate(route_records):
        first_line = LineString(first["backbone_um"])
        for second in route_records[first_index + 1:]:
            if first["layer"] != second["layer"]:
                continue
            second_line = LineString(second["backbone_um"])
            intersection = first_line.intersection(second_line)
            if intersection.is_empty:
                continue
            geometries = (
                list(intersection.geoms)
                if hasattr(intersection, "geoms")
                else [intersection]
            )
            for geometry in geometries:
                point = geometry.representative_point()
                kind = (
                    "overlap"
                    if geometry.geom_type in {"LineString", "MultiLineString"}
                    else "crossing"
                    if first_line.crosses(second_line)
                    else "touching"
                )
                route_crossings.append({
                    "route_a": {
                        "source": first["source"],
                        "target": first["target"],
                    },
                    "route_b": {
                        "source": second["source"],
                        "target": second["target"],
                    },
                    "layer": first["layer"],
                    "kind": kind,
                    "location_um": [float(point.x), float(point.y)],
                })
    return {
        "ports_by_component": ports_by_component,
        "overlaps": overlaps,
        "route_crossings": route_crossings,
        "route_endpoint_gaps": route_endpoint_gaps,
    }


def generate_preview(
    design: DesignSpec,
    output_path: Path,
    *,
    show_component_names: bool = True,
    show_port_names: bool = True,
    show_layer_info: bool = True,
    _component: gf.Component | None = None,
    _references: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an annotated PNG preview without exporting GDS or design JSON."""
    if not design.components:
        raise ValueError("cannot preview an empty design")

    if _component is None or _references is None:
        component, references = _build_component_with_references(design)
    else:
        component, references = _component, _references
    design_box = component.dbbox()
    width_um = max(float(design_box.width()), 1.0)
    height_um = max(float(design_box.height()), 1.0)
    design_aspect = width_um / height_um
    figure_width = min(24.0, max(10.0, 6.0 * design_aspect))
    figure_height = max(2.5, figure_width / design_aspect)
    figure, axis = plt.subplots(figsize=(figure_width, figure_height))
    component_labels: list[str] = []
    port_labels: list[str] = []

    layer_polygons = component.get_polygons(by="tuple")
    colour_map = plt.get_cmap("tab10")
    for colour_index, ((layer, datatype), polygons) in enumerate(
        sorted(layer_polygons.items())
    ):
        label = f"GDS {layer}/{datatype}"
        for polygon_index, polygon in enumerate(polygons):
            micron_polygon = polygon.to_dtype(gf.kcl.dbu)
            points = [
                (float(point.x), float(point.y))
                for point in micron_polygon.each_point_hull()
            ]
            if not points:
                continue
            x_values, y_values = zip(*points)
            axis.fill(
                x_values,
                y_values,
                facecolor=colour_map(colour_index % 10),
                edgecolor="black",
                linewidth=0.5,
                alpha=0.7,
                label=label if polygon_index == 0 else None,
                zorder=2,
            )

    if show_component_names:
        for name, reference in references.items():
            center = reference.dbbox().center()
            axis.annotate(
                name,
                (float(center.x), float(center.y)),
                xytext=(0, -14),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=8,
                color="black",
                bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none"},
                zorder=10,
            )
            component_labels.append(name)

    if show_port_names:
        port_label_index = 0
        for component_name, reference in references.items():
            for port in reference.ports:
                x_um, y_um = (float(value) for value in port.dcenter)
                label = f"{component_name}.{port.name}"
                orientation = float(port.orientation) % 360
                horizontal = cos(radians(orientation))
                vertical = sin(radians(orientation))
                x_offset = 7 if horizontal >= 0 else -7
                vertical_level = 7 + (port_label_index % 4) * 10
                y_offset = vertical_level if vertical >= 0 else -vertical_level
                axis.scatter([x_um], [y_um], s=14, color="red", zorder=11)
                axis.annotate(
                    label,
                    (x_um, y_um),
                    xytext=(x_offset, y_offset),
                    textcoords="offset points",
                    ha="left" if x_offset > 0 else "right",
                    va="bottom" if y_offset > 0 else "top",
                    fontsize=7,
                    color="darkred",
                    zorder=12,
                )
                port_labels.append(label)
                port_label_index += 1

    layers = [
        {"layer": int(layer), "datatype": int(datatype)}
        for layer, datatype in sorted(component.layers)
    ]
    if show_layer_info and layers:
        axis.legend(loc="best", title="Layers")
    axis.set_title(f"Design preview: {design.name}")
    axis.set_xlabel("x (µm)")
    axis.set_ylabel("y (µm)")
    axis.set_aspect("equal", adjustable="datalim")
    axis.grid(True, linestyle=":", alpha=0.35)
    axis.margins(0.15)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(figure)
    return {
        "png_path": str(output_path.resolve()),
        "component_labels": component_labels,
        "port_labels": port_labels,
        "layers": layers,
    }


def export_design(
    design: DesignSpec,
    output_dir: Path,
    output_name: str | None = None,
) -> tuple[gf.Component, Path, Path]:
    """Build a design and export GDS plus an annotated PNG preview."""
    component, references = _build_component_with_references(design)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_stem = output_name or design.name
    gds_path = output_dir / f"{file_stem}.gds"
    png_path = output_dir / f"{file_stem}.png"

    component.write_gds(gds_path)
    generate_preview(
        design,
        png_path,
        show_component_names=True,
        show_port_names=True,
        show_layer_info=True,
        _component=component,
        _references=references,
    )
    return component, gds_path, png_path
