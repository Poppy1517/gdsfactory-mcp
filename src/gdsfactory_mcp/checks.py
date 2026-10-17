"""Technology-neutral checks for a validated photonic design."""

from typing import Any

from gdsfactory_mcp.backend import get_design_analysis_data
from gdsfactory_mcp.models import DesignSpec


def run_design_checks(design: DesignSpec) -> dict[str, Any]:
    """Check connectivity and supported inter-component geometry conditions."""
    geometry = get_design_analysis_data(design)
    ports_by_component = geometry["ports_by_component"]
    connected_endpoints = {
        (connection.source_component, connection.source_port)
        for connection in design.connections
    } | {
        (connection.target_component, connection.target_port)
        for connection in design.connections
    }
    findings: list[dict[str, Any]] = []
    if not design.components:
        findings.append({
            "code": "empty_design",
            "severity": "error",
            "message": "The design contains no components.",
            "components": [],
            "ports": [],
        })

    for component_name, ports in ports_by_component.items():
        for port in ports:
            endpoint = (component_name, port["name"])
            is_external_vertical_port = port["port_type"].startswith("vertical_")
            if endpoint not in connected_endpoints and not is_external_vertical_port:
                findings.append({
                    "code": "unconnected_port",
                    "severity": "warning",
                    "message": f"Port is not connected: {component_name}.{port['name']}",
                    "components": [component_name],
                    "ports": [f"{component_name}.{port['name']}"],
                })

    seen_connections: set[frozenset[tuple[str, str]]] = set()
    used_ports: set[tuple[str, str]] = set()
    connected_component_pairs: dict[frozenset[str], set[str]] = {}
    for connection in design.connections:
        source_endpoint = (connection.source_component, connection.source_port)
        target_endpoint = (connection.target_component, connection.target_port)
        endpoint_pair = frozenset((source_endpoint, target_endpoint))
        port_labels = [
            f"{connection.source_component}.{connection.source_port}",
            f"{connection.target_component}.{connection.target_port}",
        ]
        if endpoint_pair in seen_connections:
            findings.append({
                "code": "duplicate_connection",
                "severity": "error",
                "message": f"The same connection appears more than once: {' <-> '.join(port_labels)}",
                "components": [connection.source_component, connection.target_component],
                "ports": port_labels,
            })
        seen_connections.add(endpoint_pair)
        reused = {source_endpoint, target_endpoint} & used_ports
        for component_name, port_name in sorted(reused):
            findings.append({
                "code": "port_used_multiple_times",
                "severity": "error",
                "message": f"Port is used by multiple connections: {component_name}.{port_name}",
                "components": [component_name],
                "ports": [f"{component_name}.{port_name}"],
            })
        used_ports.update((source_endpoint, target_endpoint))

        source = next(
            port
            for port in ports_by_component[connection.source_component]
            if port["name"] == connection.source_port
        )
        target = next(
            port
            for port in ports_by_component[connection.target_component]
            if port["name"] == connection.target_port
        )
        for component_name, port in (
            (connection.source_component, source),
            (connection.target_component, target),
        ):
            if port["port_type"] != "optical":
                findings.append({
                    "code": "non_optical_connection",
                    "severity": "error",
                    "message": f"Connected port is not optical: {component_name}.{port['name']}",
                    "components": [component_name],
                    "ports": [f"{component_name}.{port['name']}"],
                })
        width_difference = abs(source["width_um"] - target["width_um"])
        if width_difference > 1e-6:
            severity = "error" if connection.connection_type == "direct" else "warning"
            findings.append({
                "code": "port_width_mismatch",
                "severity": severity,
                "message": (
                    f"Connected port widths differ: {port_labels[0]} is "
                    f"{source['width_um']} µm and {port_labels[1]} is "
                    f"{target['width_um']} µm ({connection.connection_type})."
                ),
                "components": [connection.source_component, connection.target_component],
                "ports": port_labels,
            })
        pair = frozenset((connection.source_component, connection.target_component))
        connected_component_pairs.setdefault(pair, set()).add(connection.connection_type)

    for overlap in geometry["overlaps"]:
        components = [overlap["component_a"], overlap["component_b"]]
        connection_types = connected_component_pairs.get(frozenset(components), set())
        connected = bool(connection_types)
        findings.append({
            "code": (
                "connected_component_overlap" if connected
                else "unconnected_component_overlap"
            ),
            "severity": "warning" if connected else "error",
            "message": (
                f"Components {components[0]} and {components[1]} overlap by "
                f"{overlap['area_um2']:.6g} µm² on GDS layer "
                f"{overlap['layer']['layer']}/{overlap['layer']['datatype']}."
                + (
                    " They are connected, so this may be an intentional interface; verify it."
                    if connected
                    else " They are not connected, so this is treated as accidental overlap."
                )
            ),
            "components": components,
            "ports": [],
            "layer": overlap["layer"],
            "area_um2": overlap["area_um2"],
            "connection_types": sorted(connection_types),
        })

    for crossing in geometry["route_crossings"]:
        route_a = crossing["route_a"]
        route_b = crossing["route_b"]
        location_x, location_y = crossing["location_um"]
        findings.append({
            "code": "unintended_route_crossing",
            "severity": "error",
            "message": (
                f"Optical routes {route_a['source']} -> {route_a['target']} and "
                f"{route_b['source']} -> {route_b['target']} have an unintended "
                f"same-layer {crossing['kind']} near "
                f"({location_x:.3f}, {location_y:.3f}) µm on GDS layer "
                f"{crossing['layer']['layer']}/{crossing['layer']['datatype']}. "
                "Move the components, reroute the waveguides, or insert an explicit "
                "crossing component."
            ),
            "components": sorted({
                route_a["source"].split(".", 1)[0],
                route_a["target"].split(".", 1)[0],
                route_b["source"].split(".", 1)[0],
                route_b["target"].split(".", 1)[0],
            }),
            "ports": [
                route_a["source"], route_a["target"],
                route_b["source"], route_b["target"],
            ],
            "layer": crossing["layer"],
            "location_um": crossing["location_um"],
            "intersection_kind": crossing["kind"],
        })

    for gap in geometry["route_endpoint_gaps"]:
        source_gap = gap["source_gap_um"]
        target_gap = gap["target_gap_um"]
        gap_text = (
            "the route backbone is empty"
            if source_gap is None or target_gap is None
            else (
                f"the source gap is {source_gap:.6g} µm and the target gap is "
                f"{target_gap:.6g} µm"
            )
        )
        findings.append({
            "code": "disconnected_route_geometry",
            "severity": "error",
            "message": (
                f"Route geometry does not reach both registered ports for "
                f"{gap['source']} -> {gap['target']}: {gap_text}. "
                "Reroute the connection before export."
            ),
            "components": [
                gap["source"].split(".", 1)[0],
                gap["target"].split(".", 1)[0],
            ],
            "ports": [gap["source"], gap["target"]],
            "source_gap_um": source_gap,
            "target_gap_um": target_gap,
        })

    warning_count = sum(item["severity"] == "warning" for item in findings)
    error_count = sum(item["severity"] == "error" for item in findings)
    return {
        "passed": error_count == 0,
        "export_allowed": error_count == 0,
        "summary": {
            "component_count": len(design.components),
            "connection_count": len(design.connections),
            "warning_count": warning_count,
            "error_count": error_count,
        },
        "findings": findings,
        "checks_performed": [
            "unconnected_ports",
            "duplicate_connections",
            "multiple_connections_per_port",
            "connected_port_types",
            "connected_port_widths",
            "route_endpoint_geometry_continuity",
            "same_layer_inter_component_polygon_overlaps",
            "same_layer_route_crossings",
        ],
        "scope": {
            "kind": "technology_neutral",
            "overlap_method": "exact same-layer polygon intersection between component instances",
            "component_internal_geometry": (
                "Excluded from overlap findings; internal MMI, coupler, ring, and similar "
                "factory geometry is treated as one intentional component."
            ),
            "not_checked": [
                "foundry-specific design rules",
                "minimum spacing",
                "minimum feature size",
                "route-to-component overlap away from registered endpoints",
            ],
        },
    }
