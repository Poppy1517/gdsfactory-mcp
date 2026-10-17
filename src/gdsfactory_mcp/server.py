"""MCP tools that expose the photonic layout design core to an AI model."""

from math import cos, radians, sin
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from pydantic import ValidationError

from gdsfactory_mcp.backend import (
    export_design,
    generate_preview,
    get_component_placement_data,
    get_component_ports_data,
    get_route_cross_section_data,
)
from gdsfactory_mcp.component_schema import get_component_schema_data
from gdsfactory_mcp.checks import run_design_checks
from gdsfactory_mcp.design import DesignService
from gdsfactory_mcp.models import ConnectionSpec, DesignSpec, PlacementSpec, PortName
from gdsfactory_mcp.registry import (
    CATEGORY_REGISTRY,
    COMPONENT_REGISTRY,
    ComponentCategoryKey,
    IntegrationStatus,
)
from gdsfactory_mcp.units import normalize_component_parameters
from gdsfactory_mcp.technology import (
    get_cross_section_profile,
    get_technology_profile,
)

mcp = MCPServer(
    "gdsfactory-layout",
    instructions=(
        "Build a photonic layout by creating uniquely named components, "
        "connecting their optical ports, and exporting the finished design. "
        "For every completed layout request, even when the user does not ask "
        "for a preview, run check_design and export_gds, then show the returned "
        "annotated PNG preview to the user."
    ),
)

_design = DesignService("mcp_design")

def _resolve_design_path(target: str) -> Path:
    """Resolve a design name or project-local JSON path."""
    cleaned = target.strip()
    if not cleaned:
        raise ValueError("design name or path cannot be empty")

    requested = Path(cleaned)
    if requested.name == cleaned:
        requested = Path("designs") / requested
    if requested.suffix == "":
        requested = requested.with_suffix(".json")
    if requested.suffix.lower() != ".json":
        raise ValueError("design files must use the .json extension")

    project_root = Path.cwd().resolve()
    resolved = (project_root / requested).resolve() if not requested.is_absolute() else requested.resolve()
    if not resolved.is_relative_to(project_root):
        raise ValueError("design path must stay inside the project directory")
    return resolved


def _resolve_project_directory(target: str) -> Path:
    """Resolve a non-empty directory path that stays inside the project."""
    cleaned = target.strip()
    if not cleaned:
        raise ValueError("output directory cannot be empty")
    project_root = Path.cwd().resolve()
    requested = Path(cleaned)
    resolved = (project_root / requested).resolve() if not requested.is_absolute() else requested.resolve()
    if not resolved.is_relative_to(project_root):
        raise ValueError("output directory must stay inside the project directory")
    return resolved


def _summary(message: str) -> dict[str, Any]:
    """Return a JSON-compatible snapshot after a successful operation."""
    return {
        "ok": True,
        "message": message,
        "design": _design.spec.model_dump(mode="json"),
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


def _classify_error(message: str) -> tuple[str, str]:
    """Map human-readable failures to stable machine-readable error metadata."""
    lowered = message.lower()
    if "component name already exists" in lowered:
        return "name_conflict", "Choose a different unique component name."
    if "port does not exist" in lowered:
        return (
            "port_not_found",
            "Call get_component_ports to choose an existing port name.",
        )
    if "component does not exist" in lowered or "component not found" in lowered:
        return (
            "component_not_found",
            "Call get_design to choose an existing component name.",
        )
    if "connection does not exist" in lowered:
        return (
            "connection_not_found",
            "Call get_design to inspect the current connections and endpoints.",
        )
    if "invalid component parameters" in lowered or any(
        marker in lowered
        for marker in (
            "greater than 0",
            "extra inputs are not permitted",
            "unsupported parameters",
            "at least one parameter",
            "invalid length",
            "unsupported length unit",
        )
    ):
        return (
            "invalid_parameters",
            "Call get_component_schema and use the documented parameter names and limits.",
        )
    if "invalid component name" in lowered or "new_name must be different" in lowered:
        return (
            "invalid_name",
            "Use a different name beginning with a letter or underscore and containing only letters, numbers, and underscores.",
        )
    if "unsaved changes" in lowered:
        return (
            "unsaved_changes",
            "Save the current design or explicitly allow discarding unsaved changes.",
        )
    if "already exists" in lowered:
        return (
            "file_conflict",
            "Choose a different output name or explicitly enable overwrite.",
        )
    return (
        "operation_failed",
        "Check the error message, inspect the current design, and correct the input before retrying.",
    )


def _error(
    message: str,
    *,
    error_type: str | None = None,
    suggestion: str | None = None,
) -> dict[str, Any]:
    """Return one stable error envelope without changing the current design."""
    inferred_type, inferred_suggestion = _classify_error(message)
    return {
        "ok": False,
        "error_type": error_type or inferred_type,
        "error": message,
        "suggestion": suggestion or inferred_suggestion,
        "design": _design.spec.model_dump(mode="json"),
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


def _find_port(
    design: DesignSpec,
    component_name: str,
    port_name: str,
) -> dict[str, Any]:
    """Return one real placed port or raise a concise input error."""
    ports = get_component_ports_data(
        design,
        component_name,
        apply_connections=False,
    )
    for port in ports:
        if port["name"] == port_name:
            return port
    available = ", ".join(port["name"] for port in ports)
    raise ValueError(
        f"port does not exist: {component_name}.{port_name}; "
        f"available ports: {available}"
    )


def _preflight_connection(
    source_component: str,
    source_port: str,
    target_component: str,
    target_port: str,
    *,
    connection_type: str,
    cross_section: str = "strip",
    radius_um: float | None = None,
    design: DesignSpec | None = None,
) -> list[str]:
    """Check real port geometry before mutating the design."""
    validated = ConnectionSpec(
        source_component=source_component,
        source_port=source_port,
        target_component=target_component,
        target_port=target_port,
        connection_type=connection_type,
        cross_section=(
            {
                "kind": "registered_reference",
                "reference_type": "cross_section",
                "name": cross_section,
            }
            if connection_type == "route"
            else None
        ),
        radius_um=radius_um,
    )
    if validated.cross_section is not None:
        cross_section = validated.cross_section.name
    radius_um = validated.radius_um
    checked_design = design or _design.spec
    source = _find_port(checked_design, source_component, source_port)
    target = _find_port(checked_design, target_component, target_port)
    for component_name, port in (
        (source_component, source),
        (target_component, target),
    ):
        if port["port_type"] != "optical":
            raise ValueError(
                f"waveguide connection requires an optical port: "
                f"{component_name}.{port['name']} has type {port['port_type']}"
            )

    width_difference = abs(source["width_um"] - target["width_um"])
    if connection_type == "direct" and width_difference > 1e-6:
        raise ValueError(
            "direct connection requires equal port widths: "
            f"{source_component}.{source_port} is {source['width_um']} um and "
            f"{target_component}.{target_port} is {target['width_um']} um"
        )

    warnings = []
    if connection_type == "route":
        rules = get_route_cross_section_data(cross_section)
        min_radius = rules["min_radius_um"]
        if radius_um is not None and min_radius is not None and radius_um < min_radius:
            raise ValueError(
                f"radius_um {radius_um} is smaller than the {cross_section} "
                f"cross-section minimum radius {min_radius} um"
            )
        route_width = rules["width_um"]
        endpoint_widths = (source["width_um"], target["width_um"])
        if any(abs(width - route_width) > 1e-6 for width in endpoint_widths):
            warnings.append(
                f"Endpoint widths {endpoint_widths[0]} um and {endpoint_widths[1]} um "
                f"differ from the {cross_section} route width {route_width} um; "
                "automatic tapers may be added."
            )

        dx = target["center_um"][0] - source["center_um"][0]
        dy = target["center_um"][1] - source["center_um"][1]
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            raise ValueError("routed ports must not occupy the same position")
        source_angle = radians(source["orientation_deg"])
        target_angle = radians(target["orientation_deg"])
        source_toward = cos(source_angle) * dx + sin(source_angle) * dy > 0
        target_toward = cos(target_angle) * dx + sin(target_angle) * dy < 0
        if not (source_toward and target_toward):
            warnings.append(
                "The ports do not face each other directly; the route will require "
                "additional bends."
            )
    return warnings


@mcp.tool()
def get_design() -> dict[str, Any]:
    """Read current components, dimensions in micrometres, and connections without modifying the design."""
    return _summary("Retrieved the current design.")


@mcp.tool()
def list_component_types(
    category: ComponentCategoryKey | None = None,
    status: IntegrationStatus | None = None,
) -> dict[str, Any]:
    """List allowlisted component types, optionally filtered by category and status.

    Status ``integrated`` means the component can be created by a current MCP
    compatibility tool. Status ``planned`` means it is allowlisted but not yet
    connected to the generic creation workflow. This operation is read-only.
    """
    definitions = [
        definition
        for definition in COMPONENT_REGISTRY.values()
        if (category is None or definition.category == category)
        and (status is None or definition.status == status)
    ]
    if category is not None:
        category_keys = [category]
    elif status is not None:
        matched_categories = {item.category for item in definitions}
        category_keys = [
            key for key in CATEGORY_REGISTRY if key in matched_categories
        ]
    else:
        category_keys = list(CATEGORY_REGISTRY)
    categories = [
        {
            "key": item.key,
            "name_zh": item.name_zh,
            "name_en": item.name_en,
            "common_name": item.common_name,
        }
        for key in category_keys
        if (item := CATEGORY_REGISTRY[key])
    ]
    components = [
        {
            "type_name": item.type_name,
            "name_zh": item.name_zh,
            "common_name": item.common_name,
            "category": item.category,
            "factory_name": item.factory_name,
            "status": item.status,
            "available_now": item.status == "integrated",
        }
        for item in definitions
    ]
    return {
        "ok": True,
        "message": f"Found {len(components)} matching component type(s).",
        "filters": {"category": category, "status": status},
        "categories": categories,
        "components": components,
        "count": len(components),
    }


@mcp.tool()
def get_component_schema(type_name: str) -> dict[str, Any]:
    """Return parameters, defaults, units, limits, and exposure for one allowed type.

    Factory parameters reflect the installed gdsfactory version. A parameter is
    not accepted by future generic creation until generic_creation_exposed is true.
    Current compatibility tools are reported separately when available.
    """
    try:
        schema = get_component_schema_data(type_name)
    except ValueError as error:
        return _error(str(error))
    return {
        "ok": True,
        "message": f"Retrieved parameter schema for '{type_name}'.",
        "schema": schema,
    }


@mcp.tool()
def get_technology() -> dict[str, Any]:
    """Return the active PDK, declared layers, and managed cross-section defaults.

    The report distinguishes default width, default bend radius, and true minimum
    bend radius, records their runtime source, and states whether the PDK is
    foundry-qualified. This operation does not modify the current design.
    """
    try:
        technology = get_technology_profile()
    except (RuntimeError, ValueError) as error:
        return _error(f"Could not read technology profile: {error}")
    return {
        "ok": True,
        "message": (
            f"Retrieved technology profile for active PDK "
            f"'{technology['active_pdk']['name']}'."
        ),
        "technology": technology,
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


@mcp.tool()
def create_component(
    name: str,
    type_name: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an integrated allowlisted component from validated JSON parameters.

    Query get_component_schema first. Length parameters accept nm or um/µm;
    bare numbers default to nm and are converted to internal µm. Only parameters
    marked generic_creation_exposed are accepted. Invalid inputs are atomic.
    """
    try:
        normalized_parameters, unit_conversions = normalize_component_parameters(
            type_name,
            parameters or {},
        )
        component = _design.add_component(name, type_name, normalized_parameters)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        )
        return _error(f"Invalid component parameters: {details}")
    except ValueError as error:
        return _error(str(error))
    result = _summary(f"Created {type_name} component '{name}'.")
    result["created_component"] = component.model_dump(mode="json")
    result["unit_conversions"] = unit_conversions
    return result


@mcp.tool()
def get_component_ports(name: str) -> dict[str, Any]:
    """Read actual placed ports for one component without changing the design.

    Coordinates and widths use micrometres; orientation uses degrees. Layer
    includes the GDS layer number, datatype, and technology layer name.
    """
    try:
        ports = get_component_ports_data(_design.spec, name)
    except ValueError as error:
        return _error(str(error))
    return {
        "ok": True,
        "message": f"Retrieved {len(ports)} port(s) for component '{name}'.",
        "component_name": name,
        "ports": ports,
        "count": len(ports),
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


@mcp.tool()
def new_design(name: str, discard_unsaved_changes: bool = False) -> dict[str, Any]:
    """Start a named empty design, replacing the current in-memory design.

    Unsaved work blocks replacement unless discard_unsaved_changes is true.
    The new empty design itself is unsaved until save_design or export_gds runs.
    """
    global _design
    try:
        replacement = DesignService(name, has_unsaved_changes=True)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(f"Invalid design name: {details}")
    had_unsaved_changes = _design.has_unsaved_changes
    if had_unsaved_changes and not discard_unsaved_changes:
        return _error(
            "Current design has unsaved changes. Save it first or use "
            "discard_unsaved_changes=true to replace it."
        )
    _design = replacement
    result = _summary(f"Started new empty design '{name}'.")
    result["discarded_unsaved_changes"] = had_unsaved_changes
    return result


@mcp.tool()
def save_design(target: str, overwrite: bool = False) -> dict[str, Any]:
    """Save editable design JSON under a name or project-local path.

    A simple name such as ``option_a`` becomes ``designs/option_a.json``.
    Existing files are preserved unless overwrite is true. This saves design
    data only and does not create GDS or PNG geometry files.
    """
    try:
        path = _resolve_design_path(target)
        if path.exists() and not overwrite:
            return _error(
                f"Design file already exists: {path}. "
                "Use overwrite=true to replace it."
            )
        saved_path = _design.save_json(path)
    except (OSError, ValueError) as error:
        return _error(f"Could not save design: {error}")
    result = _summary(f"Saved editable design JSON to '{saved_path}'.")
    result["saved_path"] = str(saved_path.resolve())
    result["overwritten"] = overwrite
    return result


@mcp.tool()
def list_designs() -> dict[str, Any]:
    """List saved JSON designs under the project designs directory.

    Valid files include their design name and component/connection counts.
    Invalid or unreadable JSON files are reported separately. The current
    in-memory design is not modified.
    """
    project_root = Path.cwd().resolve()
    designs_dir = (project_root / "designs").resolve()
    if not designs_dir.exists():
        return {
            "ok": True,
            "message": "No saved designs found; the designs directory does not exist yet.",
            "directory": str(designs_dir),
            "designs": [],
            "invalid_files": [],
        }

    saved_designs: list[dict[str, Any]] = []
    invalid_files: list[dict[str, str]] = []
    for path in sorted(designs_dir.rglob("*.json"), key=lambda item: str(item).lower()):
        resolved = path.resolve()
        relative_path = str(path.relative_to(project_root))
        if not resolved.is_relative_to(designs_dir):
            invalid_files.append({
                "path": relative_path,
                "error": "file resolves outside the designs directory",
            })
            continue
        try:
            spec = DesignSpec.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as error:
            details = "; ".join(item["msg"] for item in error.errors())
            invalid_files.append({"path": relative_path, "error": details})
        except (OSError, UnicodeError, ValueError) as error:
            invalid_files.append({"path": relative_path, "error": str(error)})
        else:
            saved_designs.append({
                "path": relative_path,
                "design_name": spec.name,
                "component_count": len(spec.components),
                "connection_count": len(spec.connections),
            })

    return {
        "ok": True,
        "message": f"Found {len(saved_designs)} valid saved design(s).",
        "directory": str(designs_dir),
        "designs": saved_designs,
        "invalid_files": invalid_files,
    }


@mcp.tool()
def load_design(
    path: str = "build/mcp_design.json",
    discard_unsaved_changes: bool = False,
) -> dict[str, Any]:
    """Load saved design JSON by simple name or project-local path.

    A simple name such as ``option_a`` loads ``designs/option_a.json``. Loading
    replaces the current in-memory design. Unsaved work blocks replacement unless
    discard_unsaved_changes is true. Invalid files leave the current design intact.
    """
    global _design
    try:
        resolved_path = _resolve_design_path(path)
        replacement = DesignService("loading")
        replacement.load_json(resolved_path)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(f"Invalid design file: {details}")
    except (OSError, UnicodeError, ValueError) as error:
        return _error(f"Could not load design: {error}")
    had_unsaved_changes = _design.has_unsaved_changes
    if had_unsaved_changes and not discard_unsaved_changes:
        return _error(
            "Current design has unsaved changes. Save it first or use "
            "discard_unsaved_changes=true to replace it."
        )
    _design = replacement
    result = _summary(f"Loaded design from '{resolved_path}'.")
    result["loaded_path"] = str(resolved_path)
    result["discarded_unsaved_changes"] = had_unsaved_changes
    return result


@mcp.tool()
def create_straight(name: str, length_um: float, width_um: float) -> dict[str, Any]:
    """Create a straight waveguide using dimensions in micrometres."""
    try:
        _design.add_straight(name, length_um=length_um, width_um=width_um)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(
            f"Invalid component parameters: {details}",
            error_type="invalid_parameters",
        )
    except ValueError as error:
        return _error(str(error))
    return _summary(f"Created straight waveguide '{name}'.")


@mcp.tool()
def create_taper(
    name: str,
    length_um: float,
    width1_um: float,
    width2_um: float,
) -> dict[str, Any]:
    """Create a linear taper using dimensions in micrometres."""
    try:
        _design.add_taper(
            name,
            length_um=length_um,
            width1_um=width1_um,
            width2_um=width2_um,
        )
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(
            f"Invalid component parameters: {details}",
            error_type="invalid_parameters",
        )
    except ValueError as error:
        return _error(str(error))
    return _summary(f"Created taper '{name}'.")


@mcp.tool()
def update_component(
    name: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Atomically update one or more safe parameters; dimensions use micrometres.

    Parameter names match create_component. Length values accept nm or um/µm;
    bare numbers default to nm and are converted to internal µm.
    """
    warnings: list[str] = []

    def validate_existing_connections(candidate: DesignSpec) -> None:
        for connection in candidate.connections:
            connection_warnings = _preflight_connection(
                connection.source_component,
                connection.source_port,
                connection.target_component,
                connection.target_port,
                connection_type=connection.connection_type,
                cross_section=(
                    connection.cross_section.name
                    if connection.cross_section is not None
                    else "strip"
                ),
                radius_um=connection.radius_um,
                design=candidate,
            )
            warnings.extend(
                f"{connection.source_component}.{connection.source_port} -> "
                f"{connection.target_component}.{connection.target_port}: {warning}"
                for warning in connection_warnings
            )

    try:
        current = next(
            (item for item in _design.spec.components if item.name == name),
            None,
        )
        type_name = (
            current.type_name
            if current is not None and hasattr(current, "type_name")
            else current.kind
            if current is not None
            else ""
        )
        normalized_parameters, unit_conversions = normalize_component_parameters(
            type_name,
            parameters,
        )
        component = _design.update_component_parameters(
            name,
            normalized_parameters,
            validate_candidate=validate_existing_connections,
        )
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        )
        return _error(f"Invalid component parameters: {details}")
    except ValueError as error:
        return _error(str(error))
    result = _summary(
        f"Updated {len(parameters)} parameter(s) on component '{name}'."
    )
    result["updated_component"] = component.model_dump(mode="json")
    result["unit_conversions"] = unit_conversions
    result["warnings"] = warnings
    return result


@mcp.tool()
def place_component(
    name: str,
    x_um: float | None = None,
    y_um: float | None = None,
    rotation_deg: float | None = None,
    mirror_x: bool | None = None,
) -> dict[str, Any]:
    """Place, rotate, or mirror a component before direct port connections.

    Mirror is applied across the component's local X axis, followed by
    counter-clockwise rotation and translation. Omitted values keep their
    previous settings. A direct connection may subsequently move its target.
    """
    try:
        placement = _design.place_component(
            name,
            x_um=x_um,
            y_um=y_um,
            rotation_deg=rotation_deg,
            mirror_x=mirror_x,
        )
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(f"Invalid placement: {details}")
    except ValueError as error:
        return _error(str(error))
    result = _summary(f"Placed component '{name}'.")
    result["placement"] = placement.model_dump(mode="json")
    result["direct_connection_note"] = (
        "A direct port connection may move its target component."
    )
    return result


@mcp.tool()
def delete_component(
    name: str,
    delete_connections: bool = False,
) -> dict[str, Any]:
    """Delete one component; related connections require explicit confirmation."""
    try:
        component, removed_connections = _design.delete_component(
            name,
            delete_connections=delete_connections,
        )
    except ValueError as error:
        return _error(str(error))
    result = _summary(f"Deleted component '{name}'.")
    result["deleted_component"] = component.model_dump(mode="json")
    result["removed_connections"] = [
        connection.model_dump(mode="json") for connection in removed_connections
    ]
    result["removed_connection_count"] = len(removed_connections)
    return result


@mcp.tool()
def rename_component(name: str, new_name: str) -> dict[str, Any]:
    """Rename a component and atomically update all connection references."""
    try:
        component, updated_connections = _design.rename_component(name, new_name)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(f"Invalid component name: {details}")
    except ValueError as error:
        return _error(str(error))
    result = _summary(f"Renamed component '{name}' to '{new_name}'.")
    result["renamed_component"] = component.model_dump(mode="json")
    result["updated_connections"] = [
        connection.model_dump(mode="json") for connection in updated_connections
    ]
    result["updated_connection_count"] = len(updated_connections)
    return result


@mcp.tool()
def copy_component(name: str, new_name: str) -> dict[str, Any]:
    """Copy a component's type, parameters, and placement under a unique name.

    Connections are intentionally not copied, so the duplicate starts with all
    ports unconnected even though it initially overlaps the source geometry.
    """
    try:
        component = _design.copy_component(name, new_name)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(
            f"Invalid component name: {details}",
            error_type="invalid_name",
        )
    except ValueError as error:
        return _error(str(error))
    result = _summary(f"Copied component '{name}' to '{new_name}'.")
    result["copied_component"] = component.model_dump(mode="json")
    result["connections_copied"] = False
    result["placement_note"] = (
        "The copy initially overlaps the source; call place_component to move it."
    )
    return result


@mcp.tool()
def disconnect_components(
    component_a: str,
    port_a: PortName,
    component_b: str,
    port_b: PortName,
) -> dict[str, Any]:
    """Disconnect two endpoints in either order while preserving both components."""
    try:
        endpoints = {(component_a, port_a), (component_b, port_b)}
        connection = next(
            (
                item
                for item in _design.spec.connections
                if {
                    (item.source_component, item.source_port),
                    (item.target_component, item.target_port),
                }
                == endpoints
            ),
            None,
        )
        placement = None
        if connection is not None and connection.connection_type == "direct":
            placement = PlacementSpec.model_validate(
                get_component_placement_data(
                    _design.spec,
                    connection.target_component,
                )
            )
        removed = _design.disconnect_components(
            component_a,
            port_a,
            component_b,
            port_b,
            direct_target_placement=placement,
        )
    except ValueError as error:
        return _error(str(error))
    result = _summary(
        f"Disconnected {component_a}.{port_a} and {component_b}.{port_b}."
    )
    result["removed_connection"] = removed.model_dump(mode="json")
    if placement is not None:
        result["preserved_target_placement"] = placement.model_dump(mode="json")
    else:
        result["preserved_target_placement"] = None
    return result


@mcp.tool()
def connect_components(
    source_component: str,
    source_port: PortName,
    target_component: str,
    target_port: PortName,
) -> dict[str, Any]:
    """Connect two real named ports; multi-port names such as o3 are supported."""
    try:
        warnings = _preflight_connection(
            source_component,
            source_port,
            target_component,
            target_port,
            connection_type="direct",
        )
        _design.connect(
            source_component,
            source_port,
            target_component,
            target_port,
        )
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(details)
    except ValueError as error:
        return _error(str(error))
    result = _summary(
        f"Connected {source_component}.{source_port} to "
        f"{target_component}.{target_port}."
    )
    result["warnings"] = warnings
    return result


@mcp.tool()
def route_components(
    source_component: str,
    source_port: PortName,
    target_component: str,
    target_port: PortName,
    cross_section: str = "strip",
    radius_um: float | None = None,
    waypoints_um: list[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Route fixed ports, optionally through explicit [x, y] waypoints in µm."""
    try:
        warnings = _preflight_connection(
            source_component,
            source_port,
            target_component,
            target_port,
            connection_type="route",
            cross_section=cross_section,
            radius_um=radius_um,
        )
        _design.route(
            source_component,
            source_port,
            target_component,
            target_port,
            cross_section=cross_section,
            radius_um=radius_um,
            waypoints_um=waypoints_um,
        )
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(details)
    except ValueError as error:
        return _error(str(error))
    result = _summary(
        f"Routed {source_component}.{source_port} to "
        f"{target_component}.{target_port} without moving the components."
    )
    result["warnings"] = warnings
    result["cross_section_profile"] = get_cross_section_profile(cross_section)
    return result


@mcp.tool()
def preview_design(
    name: str | None = None,
    output_dir: str = "previews",
    show_component_names: bool = True,
    show_port_names: bool = True,
    show_layer_info: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Generate an annotated PNG preview without exporting GDS or editable JSON.

    Component names appear at instance centres, port names use
    ``component.port`` labels at real global coordinates, and layer information
    lists the GDS layer/datatype pairs. Existing PNG files are preserved unless
    overwrite is true. The output directory must stay inside the project.
    """
    file_stem = name or f"{_design.spec.name}_preview"
    try:
        DesignSpec(name=file_stem)
        resolved_dir = _resolve_project_directory(output_dir)
        png_path = resolved_dir / f"{file_stem}.png"
        if png_path.exists() and not overwrite:
            return _error(
                f"Preview file already exists: {png_path}. "
                "Use overwrite=true to replace it."
            )
        preview = generate_preview(
            _design.spec,
            png_path,
            show_component_names=show_component_names,
            show_port_names=show_port_names,
            show_layer_info=show_layer_info,
        )
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(
            f"Invalid preview name: {details}",
            error_type="invalid_name",
        )
    except (OSError, RuntimeError, ValueError) as error:
        return _error(f"Could not generate preview: {error}")
    return {
        "ok": True,
        "message": f"Generated annotated preview '{file_stem}'.",
        **preview,
        "show_component_names": show_component_names,
        "show_port_names": show_port_names,
        "show_layer_info": show_layer_info,
        "overwritten": overwrite,
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


@mcp.tool()
def check_design() -> dict[str, Any]:
    """Run technology-neutral connectivity and supported geometry checks.

    Warnings need review but do not block export. Errors block export. The
    report lists every performed check and explicitly records checks outside
    the current scope, such as foundry-specific spacing and feature-size rules.
    This operation does not modify or save the design.
    """
    try:
        report = run_design_checks(_design.spec)
    except (RuntimeError, ValueError) as error:
        return _error(f"Could not check design: {error}")
    return {
        "ok": True,
        "message": (
            "Design checks passed without blocking errors."
            if report["passed"]
            else "Design checks found blocking errors."
        ),
        "check_report": report,
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


@mcp.tool()
def export_gds(
    name: str | None = None,
    output_dir: str = "build",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export GDS, editable JSON, and an annotated PNG preview.

    Name defaults to the current design name. The output directory must stay
    inside the project. If any target file exists, all output is refused unless
    overwrite is true. The PNG always includes layer information, component
    names, and port names so clients can display it without a separate preview
    request.
    """
    file_stem = name or _design.spec.name
    try:
        DesignSpec(name=file_stem)
        resolved_dir = _resolve_project_directory(output_dir)
        check_report = run_design_checks(_design.spec)
        if not check_report["export_allowed"]:
            result = _error(
                "Export blocked because design checks found one or more errors.",
                error_type="design_check_failed",
                suggestion=(
                    "Review check_report.findings, correct every error-severity "
                    "finding, then run check_design and export_gds again."
                ),
            )
            result["check_report"] = check_report
            return result
        gds_path = resolved_dir / f"{file_stem}.gds"
        json_path = resolved_dir / f"{file_stem}.json"
        png_path = resolved_dir / f"{file_stem}.png"
        existing = [path for path in (gds_path, json_path, png_path) if path.exists()]
        if existing and not overwrite:
            existing_text = ", ".join(str(path) for path in existing)
            return _error(
                f"Export file already exists: {existing_text}. "
                "Use overwrite=true to replace the complete export set."
            )
        _, gds_path, png_path = export_design(
            _design.spec, resolved_dir, output_name=file_stem,
        )
        json_path = _design.save_json(json_path)
    except ValidationError as error:
        details = "; ".join(item["msg"] for item in error.errors())
        return _error(f"Invalid export name: {details}")
    except (OSError, RuntimeError, ValueError) as error:
        return _error(f"Could not export design: {error}")
    return {
        "ok": True,
        "message": f"Exported photonic layout '{file_stem}'.",
        "output_name": file_stem,
        "output_directory": str(resolved_dir),
        "gds_path": str(gds_path.resolve()),
        "json_path": str(json_path.resolve()),
        "png_path": str(png_path.resolve()),
        "preview": {
            "kind": "annotated_layout",
            "png_path": str(png_path.resolve()),
            "show_component_names": True,
            "show_port_names": True,
            "show_layer_info": True,
            "display_by_default": True,
        },
        "overwritten": overwrite,
        "check_report": check_report,
        "has_unsaved_changes": _design.has_unsaved_changes,
    }


def main() -> None:
    """Run the MCP server over standard input/output."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
